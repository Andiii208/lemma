"""成本治理测试"""

import pytest
from lemma.utils.cost_governance import CostGovernor, BudgetPolicy


class TestCostGovernor:
    def test_record_cost(self):
        gov = CostGovernor()
        gov.record("gpt-4o", 1000, 500, 0.05)
        assert gov._daily_cost == 0.05

    def test_check_budget_ok(self):
        gov = CostGovernor(BudgetPolicy(max_cost_per_run=10.0))
        gov.start_run("test")
        gov.record("gpt-4o", 1000, 500, 1.0)
        status = gov.check_budget()
        assert status["should_stop"] is False
        assert status["should_downgrade"] is False

    def test_check_budget_warning(self):
        gov = CostGovernor(BudgetPolicy(max_cost_per_run=10.0, warning_threshold=0.8))
        gov.start_run("test")
        gov.record("gpt-4o", 1000, 500, 8.5)
        status = gov.check_budget()
        assert status["should_downgrade"] is True
        assert len(status["warnings"]) > 0

    def test_check_budget_exceeded(self):
        gov = CostGovernor(BudgetPolicy(max_cost_per_run=5.0))
        gov.start_run("test")
        gov.record("gpt-4o", 1000, 500, 6.0)
        status = gov.check_budget()
        assert status["should_stop"] is True

    def test_daily_budget(self):
        gov = CostGovernor(BudgetPolicy(max_cost_per_day=10.0))
        gov.record("gpt-4o", 1000, 500, 11.0)
        status = gov.check_budget()
        assert status["should_stop"] is True

    def test_get_summary(self):
        gov = CostGovernor()
        gov.record("gpt-4o", 1000, 500, 0.05)
        summary = gov.get_summary()
        assert summary["total_records"] == 1
        assert summary["daily_cost"] == 0.05
