from unittest.mock import MagicMock, patch

import pytest
from dash import exceptions
from dash._callback_context import context_value
from dash._utils import AttributeDict

pytestmark = pytest.mark.component


def _make_config(config_id: int, name: str, page_type: str = "portfolio"):
    config = MagicMock()
    config.id = config_id
    config.name = name
    config.page_type = page_type
    config.url = f"/portfolio?saved={config_id}"
    config.created_at = MagicMock()
    config.created_at.strftime.return_value = "2026-07-02"
    return config


class TestRenderList:
    def test_anonymous_gets_login_prompt(self):
        from pages.cabinet.cabinet import render_list

        with patch("pages.cabinet.cabinet.current_user_id", return_value=None):
            result = render_list(0)
        assert "log in" in str(result).lower()

    def test_empty_list_shows_hint(self):
        from pages.cabinet.cabinet import render_list

        with (
            patch("pages.cabinet.cabinet.current_user_id", return_value=7),
            patch("pages.cabinet.cabinet.list_configs", return_value=[]) as lst,
        ):
            result = render_list(0)
        lst.assert_called_once_with(7)
        assert "no saved" in str(result).lower()

    def test_rows_contain_name_open_link_and_actions(self):
        from pages.cabinet.cabinet import render_list

        with (
            patch("pages.cabinet.cabinet.current_user_id", return_value=7),
            patch("pages.cabinet.cabinet.list_configs", return_value=[_make_config(3, "My pf")]),
        ):
            table = render_list(0)
        rendered = str(table)
        assert "My pf" in rendered
        assert "/portfolio?saved=3" in rendered
        assert "cabinet-rename" in rendered
        assert "cabinet-delete" in rendered


class TestDelete:
    def _trigger(self, triggered_id, value):
        return AttributeDict(
            triggered_inputs=[{"prop_id": f"{triggered_id}.n_clicks", "value": value}],
        )

    def test_real_click_deletes_and_bumps_refresh(self):
        from pages.cabinet.cabinet import do_delete

        token = context_value.set(self._trigger('{"index":3,"type":"cabinet-delete"}', 1))
        try:
            with (
                patch("pages.cabinet.cabinet.current_user_id", return_value=7),
                patch("pages.cabinet.cabinet.delete_config", return_value=True) as delete,
            ):
                result = do_delete([1], 0)
        finally:
            context_value.reset(token)
        delete.assert_called_once_with(7, 3)
        assert result == 1

    def test_mount_fire_with_zero_clicks_is_ignored(self):
        from pages.cabinet.cabinet import do_delete

        token = context_value.set(self._trigger('{"index":3,"type":"cabinet-delete"}', None))
        try:
            with patch("pages.cabinet.cabinet.delete_config") as delete:
                with pytest.raises(exceptions.PreventUpdate):
                    do_delete([None], 0)
        finally:
            context_value.reset(token)
        delete.assert_not_called()


class TestRename:
    def test_confirm_rename_calls_service_and_closes_modal(self):
        from pages.cabinet.cabinet import confirm_rename

        with (
            patch("pages.cabinet.cabinet.current_user_id", return_value=7),
            patch("pages.cabinet.cabinet.rename_config", return_value=True) as rename,
        ):
            is_open, refresh = confirm_rename(1, 3, "New name", 0)
        rename.assert_called_once_with(7, 3, "New name")
        assert is_open is False
        assert refresh == 1

    def test_confirm_without_click_is_prevented(self):
        from pages.cabinet.cabinet import confirm_rename

        with pytest.raises(exceptions.PreventUpdate):
            confirm_rename(0, 3, "New name", 0)
