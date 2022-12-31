from dash import dcc

db_description_text = dcc.Markdown(
    """
    Financial Database of *okama* has stock market securities, currencies, 
    commodities and indexes as well as macroeconomic indicators historical data.   
    ##### Stock markets

    - Stocks and ETF for main world markets
    - Mutual funds
    - Commodities
    - Stock indexes
    
    ##### Currencies
    
    - FX currencies
    - Crypto currencies
    - Central bank exchange rates
    
    ##### Macroeconomic indicators
    
    - Inflation (USA, United Kingdom, European Union, Israel, Russia etc.)
    - Central bank rates
    - GDP (Gross Domestic Product)
    
    ##### Other historical data
    
    - Real estate prices
    - Top bank rates
    - CAPE ratio - Shiller cyclically adjusted price-to-earnings ratio
"""
)
