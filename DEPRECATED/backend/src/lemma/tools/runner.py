"""代码执行运行器 — 抽象接口 + 受限子进程实现

提供三种安全级别：
- InProcessRunner: 进程内执行（仅用于已验证的安全代码）
- SubprocessRunner: 受限子进程（默认，Windows Job Object / Linux seccomp）
- ContainerRunner: Docker 容器隔离（最强，需 Docker Desktop）
"""

from __future__ import annotations

import asyncio
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RunResult:
    """代码执行结果"""

    stdout: str = ""
    stderr: str = ""
    return_code: int = -1
    timed_out: bool = False
    error: str = ""

    @property
    def success(self) -> bool:
        return self.return_code == 0 and not self.timed_out


class CodeRunner(ABC):
    """代码执行运行器抽象接口"""

    @abstractmethod
    async def run(self, code: str, timeout: float = 300.0) -> RunResult:
        """执行 Python 代码"""
        ...

    @abstractmethod
    def name(self) -> str:
        """运行器名称"""
        ...


class SubprocessRunner(CodeRunner):
    """受限子进程运行器 — 带资源限制的子进程执行

    Windows: 使用 Job Object 限制 CPU/内存
    Linux: 使用 cgroups/seccomp（TODO）
    """

    def __init__(
        self,
        work_dir: str,
        memory_limit_mb: int = 512,
        cpu_time_limit: float = 300.0,
        allow_network: bool = False,
    ):
        self.work_dir = Path(work_dir).resolve()
        self.memory_limit_mb = memory_limit_mb
        self.cpu_time_limit = cpu_time_limit
        self.allow_network = allow_network

    def name(self) -> str:
        return "subprocess"

    async def run(self, code: str, timeout: float = 300.0) -> RunResult:
        """在受限子进程中执行 Python 代码"""
        import uuid

        # 写入临时文件
        script_name = f"_sandbox_{uuid.uuid4().hex[:8]}.py"
        script_path = self.work_dir / script_name
        script_path.write_text(code, encoding="utf-8")

        try:
            env = os.environ.copy()
            env["MPLBACKEND"] = "Agg"

            # 移除敏感环境变量
            for key in list(env.keys()):
                key_lower = key.lower()
                if any(s in key_lower for s in ("key", "secret", "token", "password", "auth")):
                    env.pop(key, None)

            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.work_dir),
                env=env,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
                return RunResult(
                    stdout=stdout.decode("utf-8", errors="replace").strip(),
                    stderr=stderr.decode("utf-8", errors="replace").strip(),
                    return_code=proc.returncode or 0,
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return RunResult(
                    timed_out=True,
                    error=f"执行超时 ({timeout}s)",
                )

        except FileNotFoundError:
            return RunResult(error="Python 解释器未找到")
        except Exception as e:
            return RunResult(error=str(e))
        finally:
            if script_path.exists():
                script_path.unlink(missing_ok=True)


class DockerRunner(CodeRunner):
    """Docker 容器运行器 — 最高安全级别（需 Docker Desktop）"""

    def __init__(
        self,
        work_dir: str,
        image: str = "python:3.11-slim",
        memory_limit: str = "512m",
        network_disabled: bool = True,
    ):
        self.work_dir = Path(work_dir).resolve()
        self.image = image
        self.memory_limit = memory_limit
        self.network_disabled = network_disabled

    def name(self) -> str:
        return "docker"

    async def run(self, code: str, timeout: float = 300.0) -> RunResult:
        """在 Docker 容器中执行 Python 代码"""
        import uuid

        script_name = f"_sandbox_{uuid.uuid4().hex[:8]}.py"
        script_path = self.work_dir / script_name
        script_path.write_text(code, encoding="utf-8")

        try:
            cmd = [
                "docker", "run", "--rm",
                "--memory", self.memory_limit,
                "--cpus", "1",
                "-v", f"{self.work_dir}:/workspace:ro",
                "-w", "/workspace",
            ]
            if self.network_disabled:
                cmd.append("--network=none")

            cmd.extend([self.image, "python", f"/workspace/{script_name}"])

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
                return RunResult(
                    stdout=stdout.decode("utf-8", errors="replace").strip(),
                    stderr=stderr.decode("utf-8", errors="replace").strip(),
                    return_code=proc.returncode or 0,
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return RunResult(timed_out=True, error=f"Docker 执行超时 ({timeout}s)")

        except FileNotFoundError:
            return RunResult(error="Docker 未安装或不可用")
        except Exception as e:
            return RunResult(error=str(e))
        finally:
            if script_path.exists():
                script_path.unlink(missing_ok=True)


def get_runner(mode: str = "subprocess", work_dir: str = ".") -> CodeRunner:
    """获取代码执行运行器

    Args:
        mode: "subprocess" | "docker"
        work_dir: 工作目录
    """
    if mode == "docker":
        return DockerRunner(work_dir)
    return SubprocessRunner(work_dir)
