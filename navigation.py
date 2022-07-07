import dash
import dash_bootstrap_components as dbc

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Compare assets", href="/")),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("More pages", header=True),
                # dbc.DropdownMenuItem(
                #     f"{page['name']}, href={page['relative_path']}"
                # )
                # for page in dash.page_registry.values()
                dbc.DropdownMenuItem("Efficient Frontier", href="/frontier"),
                dbc.DropdownMenuItem("Compare Assets", href="/")
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
