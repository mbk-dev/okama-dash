"""E2E: macro pages auto-render their chart on load (no Submit click), navbar
dropdown navigates to them, URL params prefill, mobile viewport renders."""

import pytest

pytestmark = pytest.mark.e2e


class TestMacroAutoRender:
    def test_inflation_autorenders_bars(self, page, dash_server_url):
        page.goto(f"{dash_server_url}/macro/inflation", wait_until="domcontentloaded")
        # Default plot is annual bars; 3 default countries -> 3 bar traces.
        bars = page.locator("#infl-chart .barlayer .trace")
        bars.first.wait_for(state="attached", timeout=15_000)
        assert bars.count() == 3

    # Line charts on macro pages enable the x-axis rangeslider, which renders
    # a duplicate copy of every trace inside .rangeslider-container (verified
    # in an isolated plotly DOM probe). Scope the locator to .cartesianlayer
    # so the count equals the number of plotted series.

    def test_rates_autorenders_step_lines(self, page, dash_server_url):
        page.goto(f"{dash_server_url}/macro/rates", wait_until="domcontentloaded")
        traces = page.locator("#rates-chart .cartesianlayer .scatterlayer .js-line")
        traces.first.wait_for(state="attached", timeout=15_000)
        assert traces.count() == 3

    def test_cape10_autorenders_history_lines(self, page, dash_server_url):
        page.goto(f"{dash_server_url}/macro/cape10", wait_until="domcontentloaded")
        traces = page.locator("#cape-chart .cartesianlayer .scatterlayer .js-line")
        traces.first.wait_for(state="attached", timeout=15_000)
        assert traces.count() == 3

    def test_inflation_stats_grid_renders_percent(self, page, dash_server_url):
        page.goto(f"{dash_server_url}/macro/inflation", wait_until="domcontentloaded")
        cell = page.locator('#infl-describe-table-grid .ag-cell[col-id="RUB.INFL"]').first
        cell.wait_for(state="attached", timeout=15_000)
        assert cell.inner_text().strip().endswith("%")

    def test_inflation_download_button_present(self, page, dash_server_url):
        page.goto(f"{dash_server_url}/macro/inflation", wait_until="domcontentloaded")
        page.locator("#infl-download-data-button").wait_for(state="visible", timeout=15_000)


class TestMacroNavigationAndPrefill:
    def test_navbar_dropdown_navigates_to_macro_pages(self, page, dash_server_url):
        page.goto(dash_server_url, wait_until="domcontentloaded")
        # Scope to the navbar: the EF page body may also contain the words
        # "Macro"/"Inflation" (strict-mode collision guard).
        navbar = page.locator(".navbar")
        navbar.get_by_text("Macro", exact=True).click()
        navbar.get_by_text("Inflation", exact=True).click()
        page.wait_for_url("**/macro/inflation", timeout=10_000)

    def test_shareable_link_prefills_controls(self, page, dash_server_url):
        page.goto(
            f"{dash_server_url}/macro/inflation?tickers=RUB.INFL&plot=rolling12m",
            wait_until="domcontentloaded",
        )
        # rolling12m plot is a line chart with a rangeslider — scope to the main
        # cartesian layer (see the rangeslider note above).
        traces = page.locator("#infl-chart .cartesianlayer .scatterlayer .js-line")
        traces.first.wait_for(state="attached", timeout=15_000)
        assert traces.count() == 1  # one country from the URL

    def test_inflation_mobile_viewport(self, dash_server_url, browser):
        context = browser.new_context(viewport={"width": 375, "height": 812})
        mobile_page = context.new_page()
        mobile_page.goto(f"{dash_server_url}/macro/inflation", wait_until="domcontentloaded")

        bars = mobile_page.locator("#infl-chart .barlayer .trace")
        bars.first.wait_for(state="attached", timeout=15_000)
        assert bars.count() == 3

        mobile_page.close()
        context.close()


class TestStage2:
    def test_real_estate_autorenders_price_lines(self, page, dash_server_url):
        page.goto(f"{dash_server_url}/macro/real-estate", wait_until="domcontentloaded")
        traces = page.locator("#re-chart .cartesianlayer .scatterlayer .js-line")
        traces.first.wait_for(state="attached", timeout=15_000)
        assert traces.count() == 2  # Moscow primary + secondary defaults

    def test_real_estate_wealth_prefill_adds_inflation_line(self, page, dash_server_url):
        page.goto(
            f"{dash_server_url}/macro/real-estate?tickers=MOW_PR.RE&plot=wealth",
            wait_until="domcontentloaded",
        )
        traces = page.locator("#re-chart .cartesianlayer .scatterlayer .js-line")
        traces.first.wait_for(state="attached", timeout=15_000)
        assert traces.count() == 2  # asset + inflation reference

    def test_rates_group_switch_recalculates_reactively(self, page, dash_server_url):
        page.goto(f"{dash_server_url}/macro/rates", wait_until="domcontentloaded")
        traces = page.locator("#rates-chart .cartesianlayer .scatterlayer .js-line")
        traces.first.wait_for(state="attached", timeout=15_000)
        assert traces.count() == 3  # key-rates defaults
        # Switch the group; the chart re-renders to the single money-market default
        # without any Submit click (fully reactive chain: group -> series -> chart).
        page.locator("#rates-group").click()
        page.get_by_text("Money market RU", exact=True).click()
        page.wait_for_function(
            "() => document.querySelectorAll('#rates-chart .cartesianlayer .scatterlayer .js-line').length === 1",
            timeout=15_000,
        )

