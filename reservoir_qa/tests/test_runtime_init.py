import unittest
from unittest.mock import patch

from app.core.runtime_init import initialize_runtime


class RuntimeInitTest(unittest.TestCase):
    def test_initialize_runtime_uses_existing_services_and_data(self):
        with patch("app.core.runtime_init._ensure_parsed_artifacts", return_value="parsed") as ensure_parsed:
            with patch("app.core.runtime_init.can_connect_admin_server", return_value=True):
                with patch("app.core.runtime_init.apply_default_schema") as apply_schema:
                    with patch("app.core.runtime_init._mysql_seed_data_ready", return_value=True):
                        with patch("app.core.runtime_init.load_mysql_from_parsed_json") as load_mysql:
                            with patch("app.core.runtime_init._knowledge_ready", return_value=True):
                                with patch("app.core.runtime_init.load_knowledge") as load_knowledge:
                                    messages = initialize_runtime()

        self.assertEqual(
            messages,
            [
                "parsed",
                "MySQL server is already reachable.",
                "Schema ensured.",
                "MySQL seed data already exists.",
                "Knowledge base already exists.",
            ],
        )
        ensure_parsed.assert_called_once()
        apply_schema.assert_called_once()
        load_mysql.assert_not_called()
        load_knowledge.assert_not_called()

    def test_initialize_runtime_bootstraps_missing_services(self):
        with patch("app.core.runtime_init._ensure_parsed_artifacts", return_value="parsed"):
            with patch("app.core.runtime_init.can_connect_admin_server", return_value=False):
                with patch("app.core.runtime_init._ensure_docker_running", return_value="docker"):
                    with patch("app.core.runtime_init._ensure_mysql_container_running", return_value="mysql"):
                        with patch("app.core.runtime_init._wait_for_mysql_server", return_value="ready"):
                            with patch("app.core.runtime_init.apply_default_schema"):
                                with patch("app.core.runtime_init._mysql_seed_data_ready", return_value=False):
                                    with patch("app.core.runtime_init.load_mysql_from_parsed_json") as load_mysql:
                                        with patch("app.core.runtime_init._knowledge_ready", return_value=False):
                                            with patch("app.core.runtime_init.load_knowledge") as load_knowledge:
                                                messages = initialize_runtime()

        self.assertEqual(
            messages,
            [
                "parsed",
                "docker",
                "mysql",
                "ready",
                "Schema ensured.",
                "MySQL seed data loaded.",
                "Knowledge base loaded.",
            ],
        )
        load_mysql.assert_called_once()
        load_knowledge.assert_called_once_with(recreate=True)


if __name__ == "__main__":
    unittest.main()
