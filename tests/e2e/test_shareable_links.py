import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e

PILL_LABEL = ".mantine-Pill-label"


class TestShareableLinks:
    def test_portfolio_link_prefills_dates(self, page, dash_server_url):
        page.goto(
            f"{dash_server_url}/portfolio?tickers=AAPL.US,MSFT.US&first_date=2020-01&last_date=2024-06",
            wait_until="domcontentloaded",
        )
        first_date = page.locator("#pf-first-date")
        first_date.wait_for(state="visible", timeout=10_000)
        assert first_date.input_value() == "2020-01"
        assert page.locator("#pf-last-date").input_value() == "2024-06"

    def test_ef_link_prefills_tickers_and_dates(self, page, dash_server_url):
        page.goto(
            f"{dash_server_url}/?tickers=GOOG.US,AMZN.US&first_date=2018-06&last_date=2022-09",
            wait_until="domcontentloaded",
        )
        pills = page.locator(PILL_LABEL)
        pills.first.wait_for(state="visible", timeout=10_000)
        texts = pills.all_text_contents()
        assert "GOOG.US" in texts
        assert "AMZN.US" in texts
        assert page.locator("#ef-first-date").input_value() == "2018-06"
        assert page.locator("#ef-last-date").input_value() == "2022-09"

    def test_compare_link_prefills_tickers_and_dates(self, page, dash_server_url):
        page.goto(
            f"{dash_server_url}/compare?tickers=AAPL.US,MSFT.US&first_date=2019-03&last_date=2023-11",
            wait_until="domcontentloaded",
        )
        pills = page.locator(PILL_LABEL)
        pills.first.wait_for(state="visible", timeout=10_000)
        texts = pills.all_text_contents()
        assert "AAPL.US" in texts
        assert "MSFT.US" in texts
        assert page.locator("#al-first-date").input_value() == "2019-03"
        assert page.locator("#al-last-date").input_value() == "2023-11"

    def test_benchmark_link_prefills_tickers_and_dates(self, page, dash_server_url):
        page.goto(
            f"{dash_server_url}/benchmark?tickers=AAPL.US,TSLA.US&first_date=2017-01&last_date=2023-06",
            wait_until="domcontentloaded",
        )
        pills = page.locator(PILL_LABEL)
        pills.first.wait_for(state="visible", timeout=10_000)
        texts = pills.all_text_contents()
        assert "AAPL.US" in texts
        assert "TSLA.US" in texts
        assert page.locator("#benchmark-first-date").input_value() == "2017-01"
        assert page.locator("#benchmark-last-date").input_value() == "2023-06"

    def test_portfolio_link_prefills_mc_params(self, page, dash_server_url):
        page.goto(
            f"{dash_server_url}/portfolio?tickers=AAPL.US,MSFT.US&weights=50,50"
            f"&mc_number=100&mc_dist=t&mc_t_df=9.9&mc_t_loc=0.001&mc_t_scale=0.02&mc_var=5",
            wait_until="domcontentloaded",
        )
        # Wait for the page to settle and URL params to populate inputs
        page.locator("#pf-first-date").wait_for(state="visible", timeout=10_000)
        page.wait_for_timeout(500)  # Brief settle for reactive callback round-trip

        # MC inputs are inside a collapsed panel; Playwright reads non-visible inputs fine
        assert page.locator("#pf-monte-carlo-number").input_value() == "100"
        # Regression guard: would be "3.4" if auto-estimate overwrites
        assert page.locator("#pf-mc-t-df").input_value() == "9.9"
        assert page.locator("#pf-mc-t-var-level").input_value() == "5"

    def test_portfolio_fresh_link_auto_estimates_mc_params(self, page, dash_server_url):
        """Without MC URL params, reactive estimation must FILL the fields on load.

        Regression guard for the dead-callback bug (decorator misattached to a
        helper function): direct-call component tests stay green when the Dash
        registration is broken, so the positive auto-fill behavior must be
        asserted through the real Dash dispatch. Mock fit for norm: (0.007, 0.04).
        """
        page.goto(
            f"{dash_server_url}/portfolio?tickers=AAPL.US,MSFT.US&weights=50,50",
            wait_until="domcontentloaded",
        )
        page.locator("#pf-first-date").wait_for(state="visible", timeout=10_000)
        # expect() polls until the reactive callback round-trip fills the field
        expect(page.locator("#pf-mc-norm-mu")).to_have_value("0.007", timeout=10_000)
        assert page.locator("#pf-mc-norm-sigma").input_value() == "0.04"

    def test_portfolio_url_params_not_overwritten_by_reactive_change(self, page, dash_server_url):
        """URL MC params must survive reactive triggers like weight change (guard against auto-fit)."""
        page.goto(
            f"{dash_server_url}/portfolio?tickers=AAPL.US,MSFT.US&weights=50,50"
            f"&mc_dist=t&mc_t_df=9.9&mc_t_loc=0.0&mc_t_scale=0.02",
            wait_until="domcontentloaded",
        )
        page.locator("#pf-first-date").wait_for(state="visible", timeout=10_000)
        page.wait_for_timeout(500)

        # Verify initial values from URL (including zero-valued mc_t_loc)
        assert page.locator("#pf-mc-t-df").input_value() == "9.9"
        assert page.locator("#pf-mc-t-loc").input_value() == "0"
        assert page.locator("#pf-mc-t-scale").input_value() == "0.02"

        # Trigger reactive auto_estimate by changing weight (Input trigger)
        weight_input = page.locator("input[type='number']").first
        weight_input.click()
        weight_input.fill("60")
        page.wait_for_timeout(1500)  # Allow auto_estimate callback to fire

        # Verify URL params remain unchanged (not auto-fitted)
        assert page.locator("#pf-mc-t-df").input_value() == "9.9"
        assert page.locator("#pf-mc-t-loc").input_value() == "0"
        assert page.locator("#pf-mc-t-scale").input_value() == "0.02"
