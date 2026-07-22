"""领域市场测试"""

import zipfile
import pytest
from pathlib import Path
from lemma.tools.domain_market import DomainMarket, DomainPackage


class TestDomainMarket:
    def test_list_installed(self, tmp_path):
        # 创建模拟领域
        domain_dir = tmp_path / "test-domain"
        domain_dir.mkdir()
        (domain_dir / "domain.yaml").write_text(
            "id: test-domain\ntest: 测试领域\ndescription: A test domain",
            encoding="utf-8",
        )

        market = DomainMarket(str(tmp_path))
        installed = market.list_installed()
        assert len(installed) == 1
        assert installed[0].id == "test-domain"

    def test_list_empty(self, tmp_path):
        market = DomainMarket(str(tmp_path))
        assert market.list_installed() == []

    def test_install_from_zip(self, tmp_path):
        # 创建 zip 包
        zip_path = tmp_path / "test.ultrath-domain"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("domain.yaml", "id: packed\ntest: 打包领域\ndescription: Packed")
            zf.writestr("prompts/agent_lead.md", "# Lead")

        domains_dir = tmp_path / "domains"
        domains_dir.mkdir()

        market = DomainMarket(str(domains_dir))
        pkg = market.install_from_zip(str(zip_path))
        assert pkg is not None
        assert pkg.id == "packed"
        assert (domains_dir / "packed" / "domain.yaml").exists()

    def test_install_nonexistent(self, tmp_path):
        market = DomainMarket(str(tmp_path))
        assert market.install_from_zip("/nonexistent.zip") is None

    def test_uninstall(self, tmp_path):
        domain_dir = tmp_path / "to-remove"
        domain_dir.mkdir()
        (domain_dir / "domain.yaml").write_text("id: to-remove", encoding="utf-8")

        market = DomainMarket(str(tmp_path))
        assert market.uninstall("to-remove") is True
        assert not domain_dir.exists()

    def test_uninstall_nonexistent(self, tmp_path):
        market = DomainMarket(str(tmp_path))
        assert market.uninstall("nonexistent") is False

    def test_package_domain(self, tmp_path):
        domain_dir = tmp_path / "source" / "my-domain"
        domain_dir.mkdir(parents=True)
        (domain_dir / "domain.yaml").write_text("id: my-domain", encoding="utf-8")

        market = DomainMarket(str(tmp_path / "source"))
        output = str(tmp_path / "output.ultrath-domain")
        result = market.package_domain("my-domain", output)
        assert result is not None
        assert Path(output).exists()

        # 验证 zip 内容
        with zipfile.ZipFile(output) as zf:
            assert "domain.yaml" in zf.namelist()
