import unittest

from app.etl.tankeng_pdf_parser import parse_monthly_plan, parse_warning_rules


class TankengParserTest(unittest.TestCase):
    def test_monthly_plan_has_12_months(self):
        rows = parse_monthly_plan()
        self.assertEqual(len(rows), 12)
        self.assertEqual(rows[5].generation_10k_kwh, 20000)

    def test_warning_rules_present(self):
        rows = parse_warning_rules()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["warning_code"], "WARN_001")


if __name__ == "__main__":
    unittest.main()

