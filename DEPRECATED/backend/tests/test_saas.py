"""SaaS 多租户 + 计费测试"""

import pytest
from lemma.saas.tenant import TenantManager, Tenant
from lemma.saas.billing import BillingMeter, UsageRecord, Quota


class TestTenantManager:
    def test_create_tenant(self, tmp_path):
        mgr = TenantManager(str(tmp_path))
        t = mgr.create("Acme Corp", "acme@example.com", "pro")
        assert t.name == "Acme Corp"
        assert t.plan == "pro"
        assert len(mgr.list_all()) == 1

    def test_get_tenant(self, tmp_path):
        mgr = TenantManager(str(tmp_path))
        t = mgr.create("Test")
        assert mgr.get(t.tenant_id) is not None
        assert mgr.get("nonexistent") is None

    def test_update_plan(self, tmp_path):
        mgr = TenantManager(str(tmp_path))
        t = mgr.create("Test", plan="free")
        mgr.update_plan(t.tenant_id, "pro")
        assert mgr.get(t.tenant_id).plan == "pro"

    def test_deactivate(self, tmp_path):
        mgr = TenantManager(str(tmp_path))
        t = mgr.create("Test")
        mgr.deactivate(t.tenant_id)
        assert mgr.get(t.tenant_id).active is False

    def test_persistence(self, tmp_path):
        mgr = TenantManager(str(tmp_path))
        mgr.create("Persistent", plan="enterprise")

        mgr2 = TenantManager(str(tmp_path))
        tenants = mgr2.list_all()
        assert len(tenants) == 1
        assert tenants[0].plan == "enterprise"

    def test_tenant_limits(self):
        t = Tenant(plan="free")
        assert t.limits["max_runs_per_day"] == 5
        t2 = Tenant(plan="enterprise")
        assert t2.limits["max_runs_per_day"] == -1  # unlimited


class TestBillingMeter:
    def test_record_and_get_usage(self, tmp_path):
        meter = BillingMeter(str(tmp_path))
        meter.record(UsageRecord(tenant_id="t1", tokens_in=1000, tokens_out=500, cost_usd=0.05))

        usage = meter.get_usage_today("t1")
        assert usage["total_tokens"] == 1500
        assert usage["total_cost_usd"] == 0.05

    def test_check_quota_ok(self, tmp_path):
        meter = BillingMeter(str(tmp_path))
        meter.record(UsageRecord(tenant_id="t1", tokens_in=1000, tokens_out=0, cost_usd=0.01))

        quota = Quota(tenant_id="t1", max_tokens_per_day=100000, max_cost_per_day=5.0)
        result = meter.check_quota("t1", quota)
        assert result["exceeded"] is False

    def test_check_quota_exceeded(self, tmp_path):
        meter = BillingMeter(str(tmp_path))
        meter.record(UsageRecord(tenant_id="t1", tokens_in=200000, tokens_out=0, cost_usd=0.01))

        quota = Quota(tenant_id="t1", max_tokens_per_day=100000)
        result = meter.check_quota("t1", quota)
        assert result["exceeded"] is True

    def test_monthly_summary(self, tmp_path):
        meter = BillingMeter(str(tmp_path))
        meter.record(UsageRecord(tenant_id="t1", tokens_in=1000, cost_usd=0.05, model="gpt-4o"))
        meter.record(UsageRecord(tenant_id="t1", tokens_in=2000, cost_usd=0.10, model="gpt-4o"))

        summary = meter.get_monthly_summary("t1", 2026, 6)
        assert summary["total_tokens"] == 3000
        assert abs(summary["by_model"]["gpt-4o"] - 0.15) < 0.001
