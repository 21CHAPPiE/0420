import json
import unittest

from app.agents.answer_schema import build_answer_json, serialize_agent_content


class AnswerSchemaTest(unittest.TestCase):
    def test_build_answer_json_returns_expected_envelope(self):
        raw = build_answer_json(answer="160.00m", route="local", basis="unit-test")
        payload = json.loads(raw)
        self.assertEqual(payload["code"], 0)
        self.assertEqual(payload["message"], "ok")
        self.assertEqual(payload["data"]["answer"], "160.00m")
        self.assertEqual(payload["data"]["route"], "local")
        self.assertEqual(payload["data"]["basis"], "unit-test")
        self.assertTrue(payload["trace_id"].startswith("qa-local-"))

    def test_serialize_agent_content_falls_back_to_text_envelope(self):
        raw = serialize_agent_content("plain-text", fallback_route="rag")
        payload = json.loads(raw)
        self.assertEqual(payload["data"]["answer"], "plain-text")
        self.assertEqual(payload["data"]["route"], "rag")


if __name__ == "__main__":
    unittest.main()
