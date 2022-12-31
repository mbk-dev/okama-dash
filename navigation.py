import dash
import dash_bootstrap_components as dbc

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Database", href="/database")),
        dbc.NavItem(dbc.NavLink("Efficient Frontier", href="/")),
        dbc.NavItem(dbc.NavLink("Compare Assets", href="/compare")),
        dbc.NavItem(dbc.NavLink("Benchmark", href="/benchmark")),
        dbc.NavItem(dbc.NavLink("Portfolio", href="/portfolio")),
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
    ],
    brand="Okama widgets",
    brand_href="/",
    color="primary",
    dark=True,
)
