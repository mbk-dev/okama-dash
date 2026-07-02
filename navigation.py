import dash_bootstrap_components as dbc
from dash import Input, Output, callback

from common.auth.helpers import user_is_authenticated

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Database", href="/database")),
        dbc.NavItem(dbc.NavLink("Efficient Frontier", href="/")),
        dbc.NavItem(dbc.NavLink("Compare Assets", href="/compare")),
        dbc.NavItem(dbc.NavLink("Benchmark", href="/benchmark")),
        dbc.NavItem(dbc.NavLink("Portfolio", href="/portfolio")),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Inflation", href="/macro/inflation"),
                dbc.DropdownMenuItem("Rates", href="/macro/rates"),
                dbc.DropdownMenuItem("CAPE10", href="/macro/cape10"),
                # Real Estate temporarily hidden (live review 2026-06-08) — accumulate other-country data first.
            ],
            nav=True,
            in_navbar=True,
            label="Macro",
        ),
        dbc.DropdownMenu(
            children=[
                # dbc.DropdownMenuItem("More pages", header=True),
                # dbc.DropdownMenuItem(
                #     f"{page['name']}, href={page['relative_path']}"
                # )
                # for page in dash.page_registry.values()
                dbc.DropdownMenuItem("Community forums", href="https://community.okama.io"),
                # dbc.DropdownMenuItem("Compare Assets", href="/")
            ],
            nav=True,
            in_navbar=True,
            label="More",
        ),
        dbc.NavItem(dbc.Nav(id="navbar-auth", navbar=True)),
    ],
    brand="Okama widgets",
    brand_href="/",
    color="primary",
    dark=True,
)


@callback(Output("navbar-auth", "children"), Input("auth-url", "pathname"))
def render_auth_block(_pathname):
    # pathname changes right after login/logout redirects, so this refreshes
    # without a manual reload; fires on initial load too (no prevent_initial_call).
    if user_is_authenticated():
        return [
            dbc.NavLink("Cabinet", href="/cabinet"),
            # /logout is a Flask route — force a full page load past the Dash router.
            dbc.NavLink("Log out", href="/logout", external_link=True),
        ]
    return [
        dbc.NavLink("Log in", href="/login"),
        dbc.NavLink("Register", href="/register"),
    ]
