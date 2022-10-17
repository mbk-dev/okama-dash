from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class FinancialCrisis:
    name: str
    first_date: str
    last_date: str

    @property
    def first_date_dt(self):
        return pd.to_datetime(self.first_date, format="%Y-%m")

    @property
    def last_date_dt(self):
        return pd.to_datetime(self.last_date, format="%Y-%m")


black_monday = FinancialCrisis(name="Black Monday", first_date="1987-08", last_date="1988-08")

asian_financial_crisis = FinancialCrisis(name="Asian financial crisis", first_date="1997-07", last_date="1998-08")

dotcom_bubble = FinancialCrisis(name="Dotcom Bubble", first_date="2000-03", last_date="2002-11")

us_housing_bubble = FinancialCrisis(name="US Housing Bubble", first_date="2007-10", last_date="2009-04")

crisis_list = [black_monday, asian_financial_crisis, dotcom_bubble, us_housing_bubble]
