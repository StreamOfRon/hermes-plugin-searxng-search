"""Tests for the SearXNG plugin structure and tool handler contract."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

PLUGIN_DIR = Path(__file__).parent.parent


class TestPluginYaml:
    """Validate plugin.yaml manifest."""

    def test_file_exists(self):
        assert (PLUGIN_DIR / "plugin.yaml").exists()

    def test_valid_yaml(self):
        data = yaml.safe_load((PLUGIN_DIR / "plugin.yaml").read_text())
        assert isinstance(data, dict)

    def test_required_fields(self):
        data = yaml.safe_load((PLUGIN_DIR / "plugin.yaml").read_text())
        assert "name" in data
        assert "version" in data
        assert "provides_tools" in data
        assert isinstance(data["provides_tools"], list)
        assert len(data["provides_tools"]) > 0

    def test_tool_names_match_schemas(self):
        manifest = yaml.safe_load((PLUGIN_DIR / "plugin.yaml").read_text())
        import schemas

        schema_names = {schemas.SEARXNG_SEARCH_SCHEMA["name"]}
        for tool_name in manifest["provides_tools"]:
            assert tool_name in schema_names


class TestPluginInit:
    """Validate __init__.py has the required register function."""

    def test_file_exists(self):
        assert (PLUGIN_DIR / "__init__.py").exists()

    def test_has_register_function(self):
        import __init__ as plugin

        assert hasattr(plugin, "register")
        assert callable(plugin.register)


class TestToolSchemas:
    """Validate tool schema definitions."""

    def test_schema_has_name(self):
        import schemas

        assert schemas.SEARXNG_SEARCH_SCHEMA["name"] == "searxng_search"

    def test_schema_has_description(self):
        import schemas

        assert "description" in schemas.SEARXNG_SEARCH_SCHEMA

    def test_schema_has_parameters(self):
        import schemas

        assert "parameters" in schemas.SEARXNG_SEARCH_SCHEMA
        assert "query" in schemas.SEARXNG_SEARCH_SCHEMA["parameters"]["properties"]
        assert "limit" in schemas.SEARXNG_SEARCH_SCHEMA["parameters"]["properties"]

    def test_required_fields(self):
        import schemas

        assert schemas.SEARXNG_SEARCH_SCHEMA["parameters"]["required"] == ["query"]


class TestSearXNGSearchHandler:
    """Test searxng_search_handler functionality."""

    def test_no_config_returns_error(self):
        """Handler returns error JSON when SEARXNG_URL is not set."""
        import tools

        with patch.dict(os.environ, {}, clear=True):
            result = tools.searxng_search_handler({"query": "test query"})
            data = json.loads(result)
            assert data["success"] is False
            assert "no URL configured" in data["error"]

    def test_success_response(self):
        """Test successful SearXNG search."""
        import tools

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "title": "Result 1",
                    "url": "https://example.com/1",
                    "content": "Content 1",
                },
                {
                    "title": "Result 2",
                    "url": "https://example.com/2",
                    "content": "Content 2",
                },
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.dict(
            os.environ, {"SEARXNG_URL": "https://searx.example.com/search?q=%s"}
        ):
            with patch("httpx.Client") as mock_client:
                mock_client.return_value.__enter__.return_value.get.return_value = (
                    mock_response
                )

                result = tools.searxng_search_handler({"query": "test query", "limit": 2})
                data = json.loads(result)

                assert data["success"] is True
                assert len(data["data"]["web"]) == 2
                assert data["data"]["web"][0]["title"] == "Result 1"
                assert data["data"]["web"][0]["position"] == 1

    def test_limit_respected(self):
        """Handler should respect the limit parameter."""
        import tools

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"title": f"Result {i}", "url": f"https://example.com/{i}", "content": f"Content {i}"}
                for i in range(10)
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.dict(
            os.environ, {"SEARXNG_URL": "https://searx.example.com/search?q=%s"}
        ):
            with patch("httpx.Client") as mock_client:
                mock_client.return_value.__enter__.return_value.get.return_value = (
                    mock_response
                )

                result = tools.searxng_search_handler({"query": "test", "limit": 3})
                data = json.loads(result)
                assert len(data["data"]["web"]) == 3

    def test_api_key_header_added(self):
        """Handler should add Authorization header when SEARXNG_API_KEY is set."""
        import tools

        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()

        with patch.dict(
            os.environ,
            {
                "SEARXNG_URL": "https://searx.example.com/search?q=%s",
                "SEARXNG_API_KEY": "test-key",
            },
        ):
            with patch("httpx.Client") as mock_client:
                mock_client.return_value.__enter__.return_value.get.return_value = (
                    mock_response
                )

                tools.searxng_search_handler({"query": "test"})

                call_args = mock_client.return_value.__enter__.return_value.get.call_args
                headers = call_args.kwargs.get("headers", {})
                assert headers["Authorization"] == "Bearer test-key"

    def test_http_error_returns_error_json(self):
        """Handler should return error JSON on HTTP failure."""
        import tools

        import httpx

        with patch.dict(
            os.environ, {"SEARXNG_URL": "https://searx.example.com/search?q=%s"}
        ):
            with patch("httpx.Client") as mock_client:
                mock_client.return_value.__enter__.return_value.get.side_effect = (
                    httpx.HTTPError("Connection refused")
                )

                result = tools.searxng_search_handler({"query": "test"})
                data = json.loads(result)

                assert data["success"] is False
                assert "error" in data

    def test_handler_does_not_raise(self):
        """Handler must never raise; errors must be returned as JSON."""
        import tools

        try:
            result = tools.searxng_search_handler(None)
            data = json.loads(result)
            assert "success" in data or "error" in data
        except Exception:
            pytest.fail("Handler raised an exception instead of returning error JSON")


class TestSkillFile:
    """Validate the bundled skill file."""

    def test_skill_exists(self):
        assert (Path(__file__).parent.parent / "skill" / "SKILL.md").exists()

    def test_skill_has_frontmatter(self):
        import re

        content = (Path(__file__).parent.parent / "skill" / "SKILL.md").read_text()
        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        assert match, "SKILL.md must have YAML frontmatter"

    def test_skill_frontmatter_fields(self):
        import re

        content = (Path(__file__).parent.parent / "skill" / "SKILL.md").read_text()
        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        frontmatter = yaml.safe_load(match.group(1))

        assert "name" in frontmatter
        assert "description" in frontmatter
        assert len(frontmatter["name"]) <= 50
        assert len(frontmatter["description"]) <= 200
