"""领域市场 — 领域包的发现、安装、管理

领域包格式: .ultrath-domain (zip)
    domain.yaml
    prompts/
    knowledge/
    golden.jsonl (可选)
"""

from __future__ import annotations

import json
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class DomainPackage:
    """领域包元数据"""

    id: str
    name: str
    description: str
    version: str = "1.0.0"
    author: str = ""
    source: str = ""  # 来源 URL 或本地路径


class DomainMarket:
    """领域市场管理器"""

    def __init__(self, domains_dir: str, market_index: str | None = None):
        self.domains_dir = Path(domains_dir)
        self.market_index = market_index

    def list_installed(self) -> list[DomainPackage]:
        """列出已安装的领域"""
        packages = []
        for d in self.domains_dir.iterdir():
            if not d.is_dir():
                continue
            yaml_file = d / "domain.yaml"
            if yaml_file.exists():
                try:
                    meta = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
                    packages.append(DomainPackage(
                        id=meta.get("id", d.name),
                        name=meta.get("name", d.name),
                        description=meta.get("description", ""),
                        version=meta.get("version", "1.0.0"),
                    ))
                except Exception:
                    packages.append(DomainPackage(
                        id=d.name, name=d.name, description="(解析失败)"
                    ))
        return packages

    def install_from_zip(self, zip_path: str) -> DomainPackage | None:
        """从 zip 包安装领域"""
        zip_file = Path(zip_path)
        if not zip_file.exists():
            return None

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                # 检查是否包含 domain.yaml
                names = zf.namelist()
                yaml_name = None
                for name in names:
                    if name.endswith("domain.yaml"):
                        yaml_name = name
                        break

                if not yaml_name:
                    return None

                # 读取元数据
                meta = yaml.safe_load(zf.read(yaml_name))
                domain_id = meta.get("id", zip_file.stem)

                # 解压到目标目录
                target = self.domains_dir / domain_id
                if target.exists():
                    shutil.rmtree(target)

                zf.extractall(target)

                return DomainPackage(
                    id=domain_id,
                    name=meta.get("name", domain_id),
                    description=meta.get("description", ""),
                    version=meta.get("version", "1.0.0"),
                    source=str(zip_path),
                )
        except Exception:
            return None

    def uninstall(self, domain_id: str) -> bool:
        """卸载领域"""
        target = self.domains_dir / domain_id
        if target.exists():
            shutil.rmtree(target)
            return True
        return False

    def package_domain(self, domain_id: str, output_path: str) -> str | None:
        """打包领域为 .ultrath-domain (zip)"""
        source = self.domains_dir / domain_id
        if not source.exists():
            return None

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in source.rglob("*"):
                if file.is_file():
                    arcname = file.relative_to(source)
                    zf.write(file, arcname)

        return str(output)
