"""Human-in-the-Loop 测试"""

import asyncio
import pytest
from lemma.engine.hitl import HITLManager, ConfirmationRequest


class TestHITLManager:
    def test_create_request(self):
        mgr = HITLManager()
        req = mgr.create_request("analysis", "请确认分析结果")
        assert req.phase_id == "analysis"
        assert req.is_pending is True
        assert len(mgr.get_pending()) == 1

    def test_respond(self):
        mgr = HITLManager()
        req = mgr.create_request("analysis", "确认？")
        ok = mgr.respond(req.request_id, "approve")
        assert ok is True
        assert len(mgr.get_pending()) == 0
        assert len(mgr.get_history()) == 1
        assert mgr.get_history()[0].is_approved is True

    def test_respond_nonexistent(self):
        mgr = HITLManager()
        assert mgr.respond("nonexistent", "approve") is False

    @pytest.mark.asyncio
    async def test_wait_for_response(self):
        mgr = HITLManager()
        req = mgr.create_request("review", "审稿结果")

        async def respond_after_delay():
            await asyncio.sleep(0.1)
            mgr.respond(req.request_id, "approve")

        asyncio.create_task(respond_after_delay())
        result = await mgr.wait_for_response(req.request_id, timeout=5.0)
        assert result is not None
        assert result.is_approved is True

    @pytest.mark.asyncio
    async def test_wait_timeout(self):
        mgr = HITLManager()
        req = mgr.create_request("review", "审稿结果")

        result = await mgr.wait_for_response(req.request_id, timeout=0.1)
        assert result is not None
        assert result.response == "timeout"

    def test_custom_options(self):
        mgr = HITLManager()
        req = mgr.create_request("writing", "选择修改方式", options=["approve", "rewrite", "skip"])
        assert req.options == ["approve", "rewrite", "skip"]
