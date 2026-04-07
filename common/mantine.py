import dash_mantine_components as dmc

SEARCH_THEME = {"fontFamily": "inherit", "headings": {"fontFamily": "inherit"}}


def search_provider(children):
    return dmc.MantineProvider(children=children, theme=SEARCH_THEME)
