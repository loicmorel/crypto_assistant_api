
"""utils functions
"""
import pandas as pd
import numpy as np
import matplotlib.dates as dates
from datetime import timedelta, date

def ohlcv_to_df(klines):
    """transform ohlvc data to dataframe
    """

    klines_np = np.array(klines)
    data = pd.DataFrame(klines_np.reshape(-1, 12), dtype=float, columns=(
        'o_ts',
        'Open',
        'High',
        'Low',
        'Close',
        'Volume',
        'c_ts',
        'Quote asset volume',
        'Number of trades',
        'Taker buy base asset volume',
        'Taker buy quote asset volume',
        'Ignore')
    )
    data['o_ts'] = pd.to_datetime(data['o_ts'], unit='ms')
    data['c_ts'] = pd.to_datetime(data['c_ts'], unit='ms')
    data['o_date'] = dates.date2num(data['o_ts'])
    data.drop(columns=[
        'Quote asset volume',
        'Number of trades',
        'Taker buy base asset volume',
        'Taker buy quote asset volume',
        'Ignore'
        ], inplace=True
    )
    return data

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)
