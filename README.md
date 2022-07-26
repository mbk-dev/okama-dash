[![Python](https://img.shields.io/badge/python-v3-brightgreen.svg)](https://www.python.org/)
[![License](https://img.shields.io/pypi/l/okama.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Okama widgets
This repository has a set of interactive financial widgets (multi-page web application) build with 
[okama package](https://github.com/mbk-dev/okama/) and [Dash (plotly)](https://dash.plotly.com/) framework:

- Efficient Frontier builder
- Compare assets historical performance: wealth indexes, rate of return and risk-metrics

_okama package_ is used for quantitative finance and historical data.  
Running financial widgets example is available on [okama.io](https://okama.io).

![](../images/images/main_page.jpg?raw=true) 
## Historical data
Widgets go with free «end of day» historical stock markets data and macroeconomic indicators through 
[okama package](https://github.com/mbk-dev/okama/):

### End of day historical data

- Stocks and ETF for main world markets
- Mutual funds
- Commodities
- Stock indexes

### Currencies

- FX currencies
- Crypto currencies
- Central bank exchange rates

### Macroeconomic indicators
For many countries (USA, United Kingdom, European Union, Russia, Israel etc.):  

- Inflation
- Central bank rates
- CAPE10 (Shiller P/E) Cyclically adjusted price-to-earnings ratios

### Other historical data

- Real estate prices
- Top bank rates

## Installation
We recommend using [Poetry](https://python-poetry.org/docs/) for dependency management.  
After installing Poetry:
```python
poetry init
poetry shell  # activate the environment
```
Alternatively you can do it with pure python:
```python
python -m venv venv
source venv/bin/activate  # Windows: \venv\scripts\activate
pip install -r requirements.txt
```
To run the project locally:
```python
python app.py
```
For production, we recommend using [gunicorn](https://gunicorn.org/#docs) WSGI server and run the project with `run_gunicorn.py`.
![](../images/images/wealth_indexes.png?raw=true) 
## License

MIT
