from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.component

MODULE = "common.html_elements.save_config_div"


class TestVisibility:
    def test_hidden_for_anonymous(self):
        from common.html_elements.save_config_div import save_button_hidden

        with patch(f"{MODULE}.user_is_authenticated", return_value=False):
            assert save_button_hidden("/portfolio") is True

    def test_visible_for_authenticated(self):
        from common.html_elements.save_config_div import save_button_hidden

        with patch(f"{MODULE}.user_is_authenticated", return_value=True):
            assert save_button_hidden("/portfolio") is False


class TestDoSaveConfig:
    def test_saves_and_closes_modal(self):
        from common.html_elements.save_config_div import do_save_config

        with (
            patch(f"{MODULE}.current_user_id", return_value=7),
            patch(f"{MODULE}.save_config", return_value=(MagicMock(), None)) as save,
        ):
            is_open, feedback = do_save_config("portfolio", 1, "My pf", "/portfolio?tickers=SPY.US")
        save.assert_called_once_with(7, "My pf", "portfolio", "/portfolio?tickers=SPY.US")
        assert is_open is False
        assert feedback == ""

    def test_error_keeps_modal_open_with_message(self):
        from common.html_elements.save_config_div import do_save_config

        with (
            patch(f"{MODULE}.current_user_id", return_value=7),
            patch(f"{MODULE}.save_config", return_value=(None, "Nothing to save yet — press Submit first.")),
        ):
            is_open, feedback = do_save_config("portfolio", 1, "My pf", "")
        assert is_open is True
        assert "press Submit first" in str(feedback)

    def test_anonymous_save_is_noop(self):
        from common.html_elements.save_config_div import do_save_config

        with (
            patch(f"{MODULE}.current_user_id", return_value=None),
            patch(f"{MODULE}.save_config") as save,
        ):
            is_open, feedback = do_save_config("portfolio", 1, "My pf", "/portfolio?x=1")
        save.assert_not_called()
        assert is_open is False


class TestDivStructure:
    def test_div_is_hidden_by_default_with_prefixed_ids(self):
        from common.html_elements.save_config_div import create_save_config_div

        div = create_save_config_div("pf", "Portfolio")
        rendered = str(div)
        assert div.hidden is True
        assert "pf-save-config-button" in rendered
        assert "pf-save-config-modal" in rendered
        assert "pf-save-config-name" in rendered
