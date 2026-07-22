"""租户管理 — 多租户隔离"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4


@dataclass
class Tenant:
    """租户"""

    tenant_id: str = field(default_factory=lambda: uuid4().hex[:12])
    name: str = ""
    email: str = ""
    plan: str = "free"  # free | pro | enterprise
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    settings: dict = field(default_factory=dict)
    active: bool = True

    @property
    def limits(self) -> dict:
        """根据计划返回资源限制"""
        plans = {
            "free": {"max_runs_per_day": 5, "max_tokens_per_run": 50000, "max_domains": 2},
            "pro": {"max_runs_per_day": 50, "max_tokens_per_run": 500000, "max_domains": 10},
            "enterprise": {"max_runs_per_day": -1, "max_tokens_per_run": -1, "max_domains": -1},
        }
        return plans.get(self.plan, plans["free"])


class TenantManager:
    """租户管理器"""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._tenants_file = self.data_dir / "tenants.jsonl"
        self._tenants: dict[str, Tenant] = {}
        self._load()

    def _load(self) -> None:
        if not self._tenants_file.exists():
            return
        for line in self._tenants_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                tenant = Tenant(**data)
                self._tenants[tenant.tenant_id] = tenant
            except (json.JSONDecodeError, TypeError):
                continue

    def create(self, name: str, email: str = "", plan: str = "free") -> Tenant:
        """创建租户"""
        tenant = Tenant(name=name, email=email, plan=plan)
        self._tenants[tenant.tenant_id] = tenant
        self._save_tenant(tenant)
        return tenant

    def get(self, tenant_id: str) -> Tenant | None:
        return self._tenants.get(tenant_id)

    def list_all(self) -> list[Tenant]:
        return list(self._tenants.values())

    def update_plan(self, tenant_id: str, plan: str) -> bool:
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return False
        tenant.plan = plan
        self._save_all()
        return True

    def deactivate(self, tenant_id: str) -> bool:
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return False
        tenant.active = False
        self._save_all()
        return True

    def _save_tenant(self, tenant: Tenant) -> None:
        with open(self._tenants_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "tenant_id": tenant.tenant_id,
                "name": tenant.name,
                "email": tenant.email,
                "plan": tenant.plan,
                "created_at": tenant.created_at,
                "active": tenant.active,
            }, ensure_ascii=False) + "\n")

    def _save_all(self) -> None:
        self._tenants_file.write_text(
            "\n".join(
                json.dumps({
                    "tenant_id": t.tenant_id,
                    "name": t.name,
                    "email": t.email,
                    "plan": t.plan,
                    "created_at": t.created_at,
                    "active": t.active,
                }, ensure_ascii=False)
                for t in self._tenants.values()
            ) + "\n",
            encoding="utf-8",
        )
