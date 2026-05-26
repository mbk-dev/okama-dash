import pytest

pytestmark = pytest.mark.e2e


class TestPortfolioPageLoad:
    def test_page_title_contains_portfolio(self, portfolio_page):
        assert "portfolio" in portfolio_page.title().lower() or "/portfolio" in portfolio_page.url

    def test_submit_button_visible(self, portfolio_page):
        btn = portfolio_page.locator("#pf-submit-button")
        btn.wait_for(state="visible", timeout=10_000)
        assert btn.is_visible()

    def test_currency_dropdown_visible(self, portfolio_page):
        dropdown = portfolio_page.locator("#pf-base-currency")
        dropdown.wait_for(state="visible", timeout=10_000)
        assert dropdown.is_visible()

    def test_rebalancing_dropdown_present(self, portfolio_page):
        dropdown = portfolio_page.locator("#pf-rebalancing-period")
        dropdown.wait_for(state="attached", timeout=10_000)
        assert dropdown.count() == 1

    def test_first_date_input_visible(self, portfolio_page):
        date_input = portfolio_page.locator("#pf-first-date")
        date_input.wait_for(state="visible", timeout=10_000)
        assert date_input.is_visible()


class TestPageNavigation:
    def test_portfolio_loads(self, page, dash_server_url):
        page.goto(f"{dash_server_url}/portfolio", wait_until="networkidle")
        assert "/portfolio" in page.url

    def test_ef_loads(self, page, dash_server_url):
        page.goto(dash_server_url, wait_until="networkidle")
        assert page.locator("body").is_visible()

    def test_compare_loads(self, page, dash_server_url):
        page.goto(f"{dash_server_url}/compare", wait_until="networkidle")
        assert "/compare" in page.url

    def test_benchmark_loads(self, page, dash_server_url):
        page.goto(f"{dash_server_url}/benchmark", wait_until="networkidle")
        assert "/benchmark" in page.url

    @pytest.mark.skip(reason="Database page hangs with mocked okama — needs additional mocking in Phase 4")
    def test_database_loads(self, page, dash_server_url):
        page.goto(f"{dash_server_url}/database", wait_until="domcontentloaded")
        assert "/database" in page.url
