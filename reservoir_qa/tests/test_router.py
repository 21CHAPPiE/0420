import json
import unittest
from unittest.mock import patch

from app.agents.router import RouteDecision, ask


class RouterTest(unittest.TestCase):
    def test_uses_local_structured_answer_before_agents(self):
        with patch("app.agents.router.build_text_to_sql_agent") as build_sql_agent:
            with patch("app.agents.router.build_rag_agent") as build_rag_agent:
                answer = ask("滩坑水电站总装机容量是多少？")

        payload = json.loads(answer)
        self.assertEqual(payload["code"], 0)
        self.assertEqual(payload["message"], "ok")
        self.assertEqual(payload["data"]["answer"], "604MW（3×200MW+4MW）。")
        self.assertEqual(payload["data"]["route"], "local")
        build_sql_agent.assert_not_called()
        build_rag_agent.assert_not_called()

    def test_returns_explicit_db_error_for_sql_question_when_db_is_down(self):
        with patch(
            "app.agents.router.classify_question",
            return_value=RouteDecision(route="sql", reason="test"),
        ):
            with patch("app.agents.router.get_local_structured_answer", return_value=None):
                with patch("app.agents.router.can_connect_query_database", return_value=False):
                    with patch("app.agents.router.build_text_to_sql_agent") as build_sql_agent:
                        answer = ask("2025年6月计划来水量是多少？")

        payload = json.loads(answer)
        self.assertEqual(payload["code"], 1)
        self.assertEqual(payload["message"], "query_failed")
        self.assertIn("无法连接结构化数据库", payload["data"]["answer"])
        self.assertEqual(payload["data"]["route"], "sql")
        build_sql_agent.assert_not_called()


if __name__ == "__main__":
    unittest.main()
