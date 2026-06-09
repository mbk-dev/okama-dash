import pytest

pytestmark = pytest.mark.e2e


def _selected_pills(page):
    """Text of the currently selected value pills in the Compare MultiSelect.

    Match only the pill *root* (one element per selected value) — `[class*="Pill"]`
    also matches the nested Pill-label, double-counting each value.
    """
    return page.locator("#al-symbols-list").evaluate(
        """el => {
            const root = el.closest('[class*="MultiSelect-root"]') || document;
            return Array.from(root.querySelectorAll('[class*="Pill-root"]'))
                .map(p => p.textContent.trim())
                .filter(Boolean);
        }"""
    )


class TestTickerSearchTabSelectsTop:
    def test_tab_selects_the_top_match(self, page, dash_server_url):
        # #25: with the listbox open and at least one match, pressing Tab accepts the top
        # (best-match) option — exactly as Enter/click would — then moves focus on.
        page.goto(
            f"{dash_server_url}/compare?tickers=AAPL.US&first_date=2020-01&last_date=2024-06",
            wait_until="domcontentloaded",
        )
        search = page.locator("#al-symbols-list")
        search.click()
        search.press_sequentially("MSFT")

        # The top match shows in the open listbox.
        page.locator('[role="option"]', has_text="MSFT.US").first.wait_for(
            state="visible", timeout=10_000
        )

        search.press("Tab")

        pills = _selected_pills(page)
        assert any("MSFT.US" in p for p in pills), f"top match not selected; pills={pills}"

    def test_tab_keeps_cursor_in_search_for_next_ticker(self, page, dash_server_url):
        # A multi-ticker selector keeps the cursor in the search box after Tab, so the user
        # can type the next ticker without re-focusing — and chain several in a row.
        page.goto(
            f"{dash_server_url}/compare?tickers=AAPL.US&first_date=2020-01&last_date=2024-06",
            wait_until="domcontentloaded",
        )
        search = page.locator("#al-symbols-list")
        search.click()
        search.press_sequentially("MSFT")
        page.locator('[role="option"]', has_text="MSFT.US").first.wait_for(
            state="visible", timeout=10_000
        )
        search.press("Tab")

        # Focus stayed in the search box (it did not move to the next control).
        active_id = page.evaluate("() => document.activeElement && document.activeElement.id")
        assert active_id == "al-symbols-list", f"cursor left the search box; active={active_id}"

        # Typed WITHOUT re-targeting the input — it must land in the still-focused search.
        page.keyboard.type("GOOG")
        page.locator('[role="option"]', has_text="GOOG.US").first.wait_for(
            state="visible", timeout=10_000
        )
        page.keyboard.press("Tab")

        pills = _selected_pills(page)
        assert any("MSFT.US" in p for p in pills), f"first Tab-picked ticker missing; pills={pills}"
        assert any("GOOG.US" in p for p in pills), f"second ticker (typed without re-focus) missing; pills={pills}"

    def test_tab_with_no_match_selects_nothing(self, page, dash_server_url):
        # Acceptance: with no matches (or the dropdown closed) Tab behaves normally —
        # it moves focus and selects nothing.
        page.goto(
            f"{dash_server_url}/compare?tickers=AAPL.US&first_date=2020-01&last_date=2024-06",
            wait_until="domcontentloaded",
        )
        search = page.locator("#al-symbols-list")
        search.click()
        search.press_sequentially("ZZZZQQ")
        page.get_by_text("No matching tickers").wait_for(state="visible", timeout=10_000)

        search.press("Tab")

        pills = _selected_pills(page)
        assert pills == ["AAPL.US"], f"no-match Tab must not add a value; pills={pills}"
