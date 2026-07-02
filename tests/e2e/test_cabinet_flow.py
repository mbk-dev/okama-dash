import pytest

pytestmark = pytest.mark.e2e


def test_register_save_open_logout(page, dash_server_url):
    # --- register (auto-login + redirect to cabinet) ---
    page.goto(f"{dash_server_url}/register", wait_until="domcontentloaded")
    page.wait_for_selector("#register-email", timeout=15000)
    page.fill("#register-email", "e2e@example.com")
    page.fill("#register-password", "long-enough-pw")
    page.fill("#register-password2", "long-enough-pw")
    page.click("#register-submit")
    page.wait_for_url("**/cabinet", timeout=15000)
    page.wait_for_selector("text=No saved configurations yet", timeout=10000)
    assert page.locator("text=No saved configurations yet").is_visible()

    # --- portfolio: submit, copy link to fill URL div, then save ---
    page.goto(
        f"{dash_server_url}/portfolio?tickers=AAPL.US,MSFT.US&weights=50,50&first_date=2020-01&last_date=2024-06",
        wait_until="domcontentloaded",
    )
    page.click("#pf-submit-button")
    # Wait for charts to render
    page.locator("#pf-graf-row").wait_for(state="visible", timeout=15000)
    # Click Copy link to fill the hidden URL div (required for Save)
    page.click("#pf-copy-link-button")
    page.wait_for_function(
        "() => (document.getElementById('pf-show-url')?.textContent || '').length > 0",
        timeout=15000,
    )
    page.click("#pf-save-config-button")
    page.fill("#pf-save-config-name", "My e2e portfolio")
    page.click("#pf-save-config-confirm")
    page.wait_for_selector("#pf-save-config-modal", state="hidden", timeout=10000)

    # --- cabinet lists it; open navigates to the saved URL ---
    page.goto(f"{dash_server_url}/cabinet", wait_until="domcontentloaded")
    page.wait_for_selector("text=My e2e portfolio", timeout=15000)
    page.click("text=Open")
    page.wait_for_url("**/portfolio?*", timeout=15000)

    # --- logout; cabinet redirects anonymous visitors to login ---
    page.goto(f"{dash_server_url}/logout", wait_until="domcontentloaded")
    page.goto(f"{dash_server_url}/cabinet", wait_until="domcontentloaded")
    page.wait_for_url("**/login", timeout=15000)
