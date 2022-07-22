[![Python](https://img.shields.io/badge/python-v3-brightgreen.svg)](https://www.python.org/)
[![License](https://img.shields.io/pypi/l/okama.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Financial widgets with okama and Dash (plotly)
This repository has a set of interactive financial widgets (multi-page web application) build with _okama_ package
and _Dash framework_:

- Efficient Frontier builder (home page)
- Compare assets historical performance: wealth indexes, rate of return and risk-metrics

![](../images/images/main_page.jpg?raw=true) 
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
For production, we recommend using [gunicorn]() WSGI server and run the project with `run_gunicorn.py`.
## License

MIT
