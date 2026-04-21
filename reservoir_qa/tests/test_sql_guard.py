import unittest

from app.core.sql_guard import validate_read_only_sql


class SqlGuardTest(unittest.TestCase):
    def test_rejects_update(self):
        with self.assertRaises(ValueError):
            validate_read_only_sql("update reservoir_basic_info set reservoir_name='x'", ["reservoir_basic_info"])

    def test_rejects_non_whitelist_table(self):
        with self.assertRaises(ValueError):
            validate_read_only_sql("select * from users", ["reservoir_basic_info"])

    def test_adds_limit(self):
        sql = validate_read_only_sql(
            "select reservoir_name from reservoir_basic_info",
            ["reservoir_basic_info"],
            default_limit=20,
        )
        self.assertIn("LIMIT 20", sql.upper())


if __name__ == "__main__":
    unittest.main()

