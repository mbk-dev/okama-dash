import pytest

pytestmark = pytest.mark.e2e


class TestSubmitShowsChart:
    def test_portfolio_submit_renders_traces(self, page, dash_server_url):
        page.goto(
            f"{dash_server_url}/portfolio?tickers=AAPL.US,MSFT.US&weights=50,50&first_date=2020-01&last_date=2024-06",
            wait_until="domcontentloaded",
        )
        chart_row = page.locator("#pf-graf-row")
        assert chart_row.get_attribute("style") == "display: none;"

        page.locator("#pf-submit-button").click()
        chart_row.wait_for(state="visible", timeout=15_000)

        traces = page.locator("#pf-wealth-indexes .scatterlayer .js-line")
        traces.first.wait_for(state="attached", timeout=10_000)
        assert traces.count() >= 2

    def test_portfolio_statistics_table_shows_metric_values(self, page, dash_server_url):
        # Regression: AG Grid resolved the dotted column name (TestPF.PF) as a nested
        # path, so the metrics column rendered empty while its header was visible.
        page.goto(
            f"{dash_server_url}/portfolio?tickers=AAPL.US,MSFT.US&weights=50,50&first_date=2020-01&last_date=2024-06",
            wait_until="domcontentloaded",
        )
        page.locator("#pf-submit-button").click()

        cell = page.locator('#pf-describe-table-grid .ag-cell[col-id="TestPF.PF"]').first
        cell.wait_for(state="attached", timeout=15_000)
        assert cell.inner_text().strip() != ""

    def test_portfolio_statistics_values_are_percent_formatted(self, page, dash_server_url):
        # Regression: inline `typeof`-guarded d3 formatters are silently rejected by the
        # dash-ag-grid function-string parser, leaving raw floats in the cells. Formatting
        # must come from a real JS function in assets/dashAgGridFunctions.js.
        page.goto(
            f"{dash_server_url}/portfolio?tickers=AAPL.US,MSFT.US&weights=50,50&first_date=2020-01&last_date=2024-06",
            wait_until="domcontentloaded",
        )
        page.locator("#pf-submit-button").click()

        cell = page.locator('#pf-describe-table-grid .ag-cell[col-id="TestPF.PF"]').first
        cell.wait_for(state="attached", timeout=15_000)
        assert cell.inner_text().strip().endswith("%")

    def test_ef_submit_shows_chart(self, page, dash_server_url):
        page.goto(
            f"{dash_server_url}/?tickers=AAPL.US,MSFT.US&first_date=2020-01&last_date=2024-06",
            wait_until="domcontentloaded",
        )
        chart_row = page.locator("#ef-graf-row")
        assert chart_row.get_attribute("style") == "display: none;"

        page.locator("#ef-submit-button-state").click()
        chart_row.wait_for(state="visible", timeout=15_000)

        assert page.locator("#ef-graf svg.main-svg").count() > 0

    def test_compare_submit_renders_traces(self, page, dash_server_url):
        page.goto(
            f"{dash_server_url}/compare?tickers=AAPL.US,MSFT.US&first_date=2020-01&last_date=2024-06",
            wait_until="domcontentloaded",
        )
        chart_row = page.locator("#al-graf-row")
        assert chart_row.get_attribute("style") == "display: none;"

        page.locator("#al-submit-button").click()
        chart_row.wait_for(state="visible", timeout=15_000)

        traces = page.locator("#al-wealth-indexes .scatterlayer .js-line")
        traces.first.wait_for(state="attached", timeout=10_000)
        assert traces.count() >= 2

    def test_benchmark_submit_renders_traces(self, page, dash_server_url):
        page.goto(
            f"{dash_server_url}/benchmark?tickers=AAPL.US,MSFT.US&first_date=2020-01&last_date=2024-06",
            wait_until="domcontentloaded",
        )
        chart_row = page.locator("#benchmark-graf-row")
        assert chart_row.get_attribute("style") == "display: none;"

        page.locator("#benchmark-submit-button").click()
        chart_row.wait_for(state="visible", timeout=15_000)

        traces = page.locator("#benchmark-graph .scatterlayer .js-line")
        traces.first.wait_for(state="attached", timeout=10_000)
        assert traces.count() >= 1
