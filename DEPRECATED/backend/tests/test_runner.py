"""代码执行运行器测试"""

import pytest
from lemma.tools.runner import SubprocessRunner, DockerRunner, RunResult, get_runner


class TestSubprocessRunner:
    def test_simple_code(self):
        runner = SubprocessRunner("/tmp")
        result = runner.run("print('hello')", timeout=10)
        # asyncio.run is needed since run is async
        import asyncio
        result = asyncio.run(result)
        assert result.success is True
        assert "hello" in result.stdout

    def test_syntax_error(self):
        runner = SubprocessRunner("/tmp")
        import asyncio
        result = asyncio.run(runner.run("def f(:", timeout=10))
        assert result.success is False
        assert result.return_code != 0

    def test_timeout(self):
        runner = SubprocessRunner("/tmp")
        import asyncio
        result = asyncio.run(runner.run("import time; time.sleep(100)", timeout=0.5))
        assert result.timed_out is True

    def test_name(self):
        runner = SubprocessRunner("/tmp")
        assert runner.name() == "subprocess"


class TestDockerRunner:
    def test_name(self):
        runner = DockerRunner("/tmp")
        assert runner.name() == "docker"


class TestGetRunner:
    def test_subprocess_mode(self):
        runner = get_runner("subprocess", "/tmp")
        assert isinstance(runner, SubprocessRunner)

    def test_docker_mode(self):
        runner = get_runner("docker", "/tmp")
        assert isinstance(runner, DockerRunner)

    def test_default_mode(self):
        runner = get_runner(work_dir="/tmp")
        assert isinstance(runner, SubprocessRunner)


class TestRunResult:
    def test_success_property(self):
        r = RunResult(return_code=0)
        assert r.success is True

    def test_failure_property(self):
        r = RunResult(return_code=1)
        assert r.success is False

    def test_timeout_property(self):
        r = RunResult(timed_out=True)
        assert r.success is False
