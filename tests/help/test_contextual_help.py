"""Tests for ContextualHelpProvider."""
from docsible.formatters.help.contextual import ContextualHelpProvider


class TestContextualHelpProviderGetHelp:
    def test_get_help_for_known_error_type(self):
        help_text = ContextualHelpProvider.get_help("RoleNotFoundError")
        assert help_text is not None
        assert len(help_text) > 0

    def test_get_help_for_file_not_found(self):
        help_text = ContextualHelpProvider.get_help("FileNotFoundError")
        assert help_text is not None

    def test_get_help_for_click_exception(self):
        help_text = ContextualHelpProvider.get_help("ClickException")
        assert help_text is not None

    def test_get_help_for_unknown_error_type_returns_none(self):
        help_text = ContextualHelpProvider.get_help("SomeMadeUpError")
        assert help_text is None

    def test_get_help_returns_string(self):
        help_text = ContextualHelpProvider.get_help("RoleNotFoundError")
        assert isinstance(help_text, str)

    def test_get_help_for_role_not_found_contains_guidance(self):
        help_text = ContextualHelpProvider.get_help("RoleNotFoundError")
        # Should contain actionable guidance
        assert help_text is not None
        assert len(help_text.strip()) > 0

    def test_get_help_for_file_not_found_returns_string(self):
        help_text = ContextualHelpProvider.get_help("FileNotFoundError")
        assert isinstance(help_text, str)

    def test_error_help_dict_has_expected_keys(self):
        # All entries in ERROR_HELP should have 'message' and 'help' keys
        for error_type, data in ContextualHelpProvider.ERROR_HELP.items():
            assert "message" in data, f"Missing 'message' for {error_type}"
            assert "help" in data, f"Missing 'help' for {error_type}"


class TestContextualHelpProviderFormatError:
    def test_format_known_error_includes_help(self):
        class RoleNotFoundError(Exception):
            pass
        error = RoleNotFoundError("role not found")
        result = ContextualHelpProvider.format_error_with_help(error)
        assert "Error:" in result
        assert "role not found" in result
        # Should include contextual help (longer than just the bare error line)
        assert len(result) > 50

    def test_format_unknown_error_still_shows_message(self):
        class UnknownError(Exception):
            pass
        error = UnknownError("something went wrong")
        result = ContextualHelpProvider.format_error_with_help(error)
        assert "Error:" in result
        assert "something went wrong" in result

    def test_format_file_not_found_includes_help(self):
        error = FileNotFoundError("no such file")
        result = ContextualHelpProvider.format_error_with_help(error)
        assert "Error:" in result
        assert len(result) > 30

    def test_format_error_returns_string(self):
        error = ValueError("bad value")
        result = ContextualHelpProvider.format_error_with_help(error)
        assert isinstance(result, str)

    def test_format_known_error_is_longer_than_unknown(self):
        # Known errors should have contextual help appended, making output longer
        class RoleNotFoundError(Exception):
            pass
        class UnknownCustomError(Exception):
            pass
        known = ContextualHelpProvider.format_error_with_help(RoleNotFoundError("msg"))
        unknown = ContextualHelpProvider.format_error_with_help(UnknownCustomError("msg"))
        assert len(known) > len(unknown)

    def test_format_error_always_includes_error_label(self):
        errors = [
            ValueError("val error"),
            FileNotFoundError("missing file"),
            RuntimeError("runtime failure"),
        ]
        for error in errors:
            result = ContextualHelpProvider.format_error_with_help(error)
            assert "Error:" in result, f"Missing 'Error:' prefix for {type(error).__name__}"


class TestContextualHelpProviderSupportedTypes:
    def test_get_supported_error_types_returns_list(self):
        types = ContextualHelpProvider.get_supported_error_types()
        assert isinstance(types, list)
        assert len(types) > 0

    def test_known_types_in_supported(self):
        types = ContextualHelpProvider.get_supported_error_types()
        assert "RoleNotFoundError" in types
        assert "FileNotFoundError" in types

    def test_click_exception_in_supported(self):
        types = ContextualHelpProvider.get_supported_error_types()
        assert "ClickException" in types

    def test_all_supported_types_have_help(self):
        types = ContextualHelpProvider.get_supported_error_types()
        for t in types:
            help_text = ContextualHelpProvider.get_help(t)
            assert help_text is not None, f"No help for {t}"

    def test_supported_types_match_error_help_keys(self):
        types = ContextualHelpProvider.get_supported_error_types()
        assert set(types) == set(ContextualHelpProvider.ERROR_HELP.keys())
