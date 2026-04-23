import unittest

from app.agents.local_structured_answer import get_local_structured_answer


class LocalStructuredAnswerTest(unittest.TestCase):
    def test_answers_installed_capacity_from_local_json(self):
        answer = get_local_structured_answer("滩坑水电站总装机容量是多少？")
        self.assertEqual(answer, "604MW（3×200MW+4MW）。")

    def test_answers_authority_question_from_reference_bank(self):
        answer = get_local_structured_answer("青田鹤城水文站遭遇50年一遇及以上洪水时，滩坑水库由谁调度？")
        self.assertEqual(answer, "由省水利厅调度。")

    def test_answers_plan_question_from_reference_bank(self):
        answer = get_local_structured_answer("滩坑水电站2025年计划年降雨量是多少？")
        self.assertEqual(answer, "1560mm。")

    def test_answers_history_question_from_reference_bank(self):
        answer = get_local_structured_answer("2024061623号洪水的最高水位是多少？")
        self.assertEqual(answer, "159.40m。")

    def test_answers_dispatch_principle_question_from_reference_bank(self):
        answer = get_local_structured_answer("库水位超过161.50m后，水库应如何调度？")
        self.assertEqual(answer, "应逐渐开启溢洪道闸门直至全开。")

    def test_answers_operation_rule_question_from_reference_bank(self):
        answer = get_local_structured_answer("溢洪道闸门的开启顺序是什么？")
        self.assertEqual(answer, "开启顺序为：#1→#6→#3→#4→#2→#5。")

    def test_answers_warning_question_from_reference_bank(self):
        answer = get_local_structured_answer("高水位预警的触发条件是什么？")
        self.assertEqual(
            answer,
            "当滩坑水库蓄水位超过土地征用线（坝前水位160.00m），且预报滩坑水库最高水位将达到移民线（坝前水位161.50m）时，触发高水位预警。",
        )

    def test_answers_control_index_question_from_reference_bank(self):
        answer = get_local_structured_answer("滩坑水库台汛期限制水位是多少？")
        self.assertEqual(answer, "156.50m。")

    def test_answers_event_inflow_question_from_event_table(self):
        answer = get_local_structured_answer("2007081917事件在2007-08-19 08:00的入流量是多少？")
        self.assertEqual(answer, "440m3/s。")

    def test_answers_event_outflow_question_from_event_table(self):
        answer = get_local_structured_answer("2007081917事件在2007-08-19 08:00的出流量是多少？")
        self.assertEqual(answer, "700m3/s。")

    def test_does_not_force_fact_answer_for_explanatory_question(self):
        answer = get_local_structured_answer("为什么设计保证出力不是总装机容量？")
        self.assertIsNone(answer)


if __name__ == "__main__":
    unittest.main()
