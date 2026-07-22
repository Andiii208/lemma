"""模糊测试器单元测试"""

import pytest
from lemma.quality.fuzzer import APIFuzzer, FuzzResult


class TestAPIFuzzer:
    def test_fuzzer_creation(self):
        fuzzer = APIFuzzer()
        assert fuzzer is not None

    def test_generate_string_inputs(self):
        fuzzer = APIFuzzer()
        inputs = fuzzer.generate_string_inputs()
        assert isinstance(inputs, list)
        assert len(inputs) > 0
        assert all(isinstance(v, str) for v in inputs)

    def test_generate_number_inputs(self):
        fuzzer = APIFuzzer()
        inputs = fuzzer.generate_number_inputs()
        assert isinstance(inputs, list)
        assert len(inputs) > 0
        assert all(isinstance(v, str) for v in inputs)

    def test_generate_json_inputs(self):
        fuzzer = APIFuzzer()
        inputs = fuzzer.generate_json_inputs()
        assert isinstance(inputs, list)
        assert len(inputs) > 0

    def test_generate_all(self):
        fuzzer = APIFuzzer()
        inputs = fuzzer.generate_all()
        assert isinstance(inputs, list)
        assert len(inputs) >= 20
        for item in inputs:
            assert "type" in item
            assert "value" in item

    def test_fuzz_result_dataclass(self):
        result = FuzzResult(
            input_type="string",
            input_value="test",
            endpoint="/api/chat",
            status_code=400,
            crashed=False,
        )
        assert result.input_type == "string"
        assert result.endpoint == "/api/chat"
        assert result.crashed is False

    def test_overlong_string(self):
        fuzzer = APIFuzzer()
        assert len(fuzzer.OVERLONG_STRING) == 100000

    def test_special_chars_contains_special(self):
        fuzzer = APIFuzzer()
        assert "!" in fuzzer.SPECIAL_CHARS
        assert "<" in fuzzer.SPECIAL_CHARS

    def test_generate_all_types_present(self):
        fuzzer = APIFuzzer()
        inputs = fuzzer.generate_all()
        types = {item["type"] for item in inputs}
        assert "string" in types
        assert "number" in types
        assert "json" in types
