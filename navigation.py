import dash_bootstrap_components as dbc

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Page 1", href="/")),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("More pages", header=True),
                dbc.DropdownMenuItem("Page 1", href="/analytics"),
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
