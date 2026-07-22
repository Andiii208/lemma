"""模糊测试框架 — 对 API/WebSocket 端点进行畸形输入测试"""

from __future__ import annotations

import json
import random
import string
from dataclasses import dataclass, field


@dataclass
class FuzzResult:
    """模糊测试结果"""

    input_type: str = ""
    input_value: str = ""
    endpoint: str = ""
    status_code: int = 0
    error: str = ""
    crashed: bool = False


class APIFuzzer:
    """API 模糊测试器"""

    # 畸形输入模板
    OVERLONG_STRING = "A" * 100000
    EMPTY_STRING = ""
    SPECIAL_CHARS = "!@#$%^&*()[]{}|\\:;'\"<>?/~`"
    UNICODE_BOMB = "你好世界" * 1000 + "🎉🚀💻" * 500
    SQL_INJECTION = "'; DROP TABLE users; --"
    XSS_PAYLOAD = "<script>alert('xss')</script>"
    NULL_BYTES = "\x00\x00\x00"
    NEGATIVE_NUMBERS = "-999999999"
    FLOAT_EDGE = "3.14159265358979323846"
    JSON_NESTED = json.dumps({"a": {"b": {"c": "d" * 10000}}})

    def generate_string_inputs(self) -> list[str]:
        """生成字符串畸形输入"""
        return [
            self.OVERLONG_STRING,
            self.EMPTY_STRING,
            self.SPECIAL_CHARS,
            self.UNICODE_BOMB,
            self.SQL_INJECTION,
            self.XSS_PAYLOAD,
            self.NULL_BYTES,
            "".join(random.choices(string.printable, k=10000)),
        ]

    def generate_number_inputs(self) -> list[str]:
        """生成数值畸形输入"""
        return [
            "0",
            "-1",
            self.NEGATIVE_NUMBERS,
            "999999999999999999",
            self.FLOAT_EDGE,
            "NaN",
            "Infinity",
            "null",
            "undefined",
            "",
        ]

    def generate_json_inputs(self) -> list[str]:
        """生成 JSON 畸形输入"""
        return [
            "{}",
            "[]",
            "null",
            "undefined",
            "not json",
            '{"key": null}',
            '{"key": ""}',
            self.JSON_NESTED,
            '{"key": "' + "A" * 50000 + '"}',
            "{'single': 'quotes'}",
        ]

    def generate_all(self) -> list[dict]:
        """生成所有畸形输入"""
        inputs = []
        for val in self.generate_string_inputs():
            inputs.append({"type": "string", "value": val})
        for val in self.generate_number_inputs():
            inputs.append({"type": "number", "value": val})
        for val in self.generate_json_inputs():
            inputs.append({"type": "json", "value": val})
        return inputs
