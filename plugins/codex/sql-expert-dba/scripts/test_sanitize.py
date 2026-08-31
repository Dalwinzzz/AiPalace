#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


class TestSanitize(unittest.TestCase):

    def setUp(self):
        import sanitize
        self.sanitize = sanitize

    def test_phone_blocked(self):
        result = self.sanitize.check("联系方式 13812345678 请查收")
        self.assertFalse(result.ok)
        self.assertIn("phone", result.pattern)

    def test_email_blocked(self):
        result = self.sanitize.check("发邮件到 user@example.com 确认")
        self.assertFalse(result.ok)
        self.assertIn("email", result.pattern)

    def test_id_card_blocked(self):
        result = self.sanitize.check("身份证 110101199003074512 核验")
        self.assertFalse(result.ok)
        self.assertIn("id_card", result.pattern)

    def test_ip_blocked(self):
        result = self.sanitize.check("服务器 192.168.1.100 上的 MySQL")
        self.assertFalse(result.ok)
        self.assertIn("ip", result.pattern)

    def test_clean_text_passes(self):
        result = self.sanitize.check("VARCHAR字段与数字比较导致索引失效")
        self.assertTrue(result.ok)

    def test_allow_token_bypasses_block(self):
        result = self.sanitize.check("13812345678", allow_tokens=["13812345678"])
        self.assertTrue(result.ok)

    def test_forbidden_token_blocks(self):
        result = self.sanitize.check("orders表的amount字段", forbidden_tokens=["orders"])
        self.assertFalse(result.ok)
        self.assertIn("forbidden_token", result.pattern)

    def test_biz_rules_scope_not_scanned(self):
        result = self.sanitize.check("13812345678", biz_rules=True)
        self.assertTrue(result.ok)

    def test_biz_rules_forbidden_token_still_blocks(self):
        result = self.sanitize.check("orders表", forbidden_tokens=["orders"], biz_rules=True)
        self.assertFalse(result.ok)


if __name__ == "__main__":
    unittest.main()
