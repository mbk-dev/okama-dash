import pytest

from common.auth.service import (
    create_user,
    delete_config,
    list_configs,
    rename_config,
    save_config,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def two_users(auth_app):
    owner, _ = create_user("owner@b.co", "long-enough-pw")
    other, _ = create_user("other@b.co", "long-enough-pw")
    return owner, other


class TestSaveConfig:
    def test_saves_and_lists_newest_first(self, two_users):
        owner, _ = two_users
        save_config(owner.id, "First", "portfolio", "/portfolio?tickers=SPY.US")
        save_config(owner.id, "Second", "ef", "/?tickers=SPY.US")
        names = [c.name for c in list_configs(owner.id)]
        assert names == ["Second", "First"]

    def test_rejects_empty_name(self, two_users):
        owner, _ = two_users
        config, error = save_config(owner.id, "  ", "portfolio", "/portfolio?x=1")
        assert config is None
        assert "name" in error.lower()

    def test_rejects_unknown_page_type(self, two_users):
        owner, _ = two_users
        config, error = save_config(owner.id, "X", "macro", "/macro/inflation")
        assert config is None
        assert "page type" in error.lower()

    def test_rejects_empty_url(self, two_users):
        owner, _ = two_users
        config, error = save_config(owner.id, "X", "portfolio", "")
        assert config is None
        assert error == "Nothing to save yet — press Submit first."


class TestOwnershipScoping:
    def test_list_is_scoped_to_user(self, two_users):
        owner, other = two_users
        save_config(owner.id, "Mine", "portfolio", "/portfolio?x=1")
        assert list_configs(other.id) == []

    def test_delete_other_users_config_fails(self, two_users):
        owner, other = two_users
        config, _ = save_config(owner.id, "Mine", "portfolio", "/portfolio?x=1")
        assert delete_config(other.id, config.id) is False
        assert [c.id for c in list_configs(owner.id)] == [config.id]

    def test_rename_other_users_config_fails(self, two_users):
        owner, other = two_users
        config, _ = save_config(owner.id, "Mine", "portfolio", "/portfolio?x=1")
        assert rename_config(other.id, config.id, "Stolen") is False
        assert list_configs(owner.id)[0].name == "Mine"


class TestRenameDelete:
    def test_rename_own_config(self, two_users):
        owner, _ = two_users
        config, _ = save_config(owner.id, "Old", "portfolio", "/portfolio?x=1")
        assert rename_config(owner.id, config.id, "New") is True
        assert list_configs(owner.id)[0].name == "New"

    def test_rename_to_blank_fails(self, two_users):
        owner, _ = two_users
        config, _ = save_config(owner.id, "Old", "portfolio", "/portfolio?x=1")
        assert rename_config(owner.id, config.id, "   ") is False

    def test_delete_own_config(self, two_users):
        owner, _ = two_users
        config, _ = save_config(owner.id, "Mine", "portfolio", "/portfolio?x=1")
        assert delete_config(owner.id, config.id) is True
        assert list_configs(owner.id) == []
