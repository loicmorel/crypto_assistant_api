
"""Data collection and management
"""

import os
import pandas as pd
import numpy as np
import matplotlib.dates as mdates
from app.config import Config
from app.exchanges.binance import Binance
from app.data_mgt.gcpmgt import Gcp
from os import listdir
from os.path import isfile, join

def collect_historical_data(exchange, symbol, freq, start_date, end_date):
    # return -1

    print('# get historical data =>', symbol, freq, 'form',
            start_date, 'to', end_date)
    klines = exchange.get_historical_data(
        symbol, freq, start_date, end_date)
    if not klines:
        print('Error: downloading klines', symbol, freq)
        return 0, -1
    klines_ = np.array(klines)
    data = pd.DataFrame(klines_.reshape(-1, 12), dtype=float, columns=(
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
    data.drop(columns=[
        'Ignore'
        ], inplace=True
    )

    return data, 0

def ohlcv_from_csv_to_df(file):
    data = pd.read_csv(f'{file}')
    data['o_ts'] = pd.to_datetime(data['o_ts'], unit='ms')
    data['c_ts'] = pd.to_datetime(data['c_ts'], unit='ms')
    data['o_date'] = mdates.date2num(data['o_ts'])
    data.drop(columns=[
        'Quote asset volume',
        'Number of trades',
        'Taker buy base asset volume',
        'Taker buy quote asset volume',
        ], inplace=True
    )
    return data

def get_all_data(gcp, config):
    data_folder = config.project.get('bucket_data_folder')
    files_d = gcp.list_files(data_folder)
    for file in files_d:
        file_ = os.path.basename(file)
        if not os.path.isfile(f'{data_folder}/{file_}'):
            gcp.load_data(file_, data_folder)

    models_folder = config.project.get('bucket_models_folder')
    files_m = gcp.list_files(models_folder)
    for file in files_m:
        file_ = os.path.basename(file)
        if not os.path.isfile(f'{models_folder}/{file_}'):
            gcp.load_data(file_, models_folder)

    return files_d + files_m

def data_collection(gcp, config):

    # get all avalable data first
    get_all_data(gcp, config)

    data_folder = config.project.get('bucket_data_folder')

    # connect to exchange
    binance = Binance(config)
    print('binance exchange connection status:', binance.get_status())

    ## collect historical data for LeWagon project and create files in raw_data dir.
    assets_list = [
        ['BTC', '1h', '1d'],
        ['ETH', '1h', '1d'],
        ['SOL', '1h', '1d'],
        ['AAVE', '1h', '1d'],
        ['DOT', '1h', '1d'],
        ['NEAR', '1h', '1d'],
        ['FTM', '1h', '1d'],
        ['VITE', '1h', '1d'],
        ['ADA', '1h', '1d']
        # ['ETH', '1m']
    ]

    # check existing local files first before downloading
    files = [f for f in listdir(data_folder) if isfile(join(data_folder, f))]

    dl_asset = []
    for assets_meta in assets_list:
        for freq in assets_meta[1:]:
            symbol = assets_meta[0] + 'USDT'

            for file in files:
                list_of_metadata = file.split('_')
                metadata = {
                    'symbol' : list_of_metadata[1],
                    'frequency' : list_of_metadata[2],
                    'start_ts' : list_of_metadata[4],
                    'end_ts' : list_of_metadata[6].rsplit( ".", 1 )[0]
                }
                if symbol == metadata['symbol'] and freq == metadata['frequency']:
                    start_date = int(metadata['end_ts'])
                    end_date = 'now'
                    data_b, ret = collect_historical_data(
                        binance, symbol, freq, start_date, end_date)
                    if ret != -1:
                        dl_asset.append([symbol, freq])
                        data_a = pd.read_csv(f'{data_folder}/{file}')
                        data_m = data_a[:-1].merge(data_b, how='outer')

                        first_ts = int(data_m['o_ts'].iloc[0])
                        last_ts = int(data_m['o_ts'].iloc[-1])
                        path = f'{data_folder}/ohlcv_{symbol}_{freq}_from_{first_ts}_to_{last_ts}.csv'
                        print('saving klines to:', path)
                        data_m.to_csv(path, index=None)

                        # remove old file
                        if os.path.exists(f'{data_folder}/{file}') \
                            and f'{data_folder}/{file}' != f'{path}':
                            print('remove file:', f'{data_folder}/{file}')
                            os.remove(f'{data_folder}/{file}')
                            gcp.delete_file(f'{data_folder}/{file}')

                        gcp.save_data(path, keep_localy=True)

    for assets_meta in assets_list:
        for freq in assets_meta[1:]:
            symbol = assets_meta[0] + 'USDT'
            if [symbol, freq] not in dl_asset:
                # start_date = '2_years_ago'
                start_date = '1_month_ago'
                end_date = 'now'
                data_b, ret = collect_historical_data(
                        binance, symbol, freq, start_date, end_date)
                if ret != -1:
                    dl_asset.append([symbol, freq])
                    first_ts = int(data_b['o_ts'].iloc[0])
                    last_ts = int(data_b['o_ts'].iloc[-1])
                    path = f'{data_folder}/ohlcv_{symbol}_{freq}_from_{first_ts}_to_{last_ts}.csv'
                    print('saving klines to:', path)
                    data_b.to_csv(path, index=None)
                    gcp.save_data(path, keep_localy=True)

    return dl_asset

if __name__ == "__main__":
    import sys

    args = sys.argv[1:]

    if len(args) >= 1:
        # print(args[0])
        pass
    else:
        print('Error: unknow arguments...')
        exit(1)

    # get config
    config = Config()

    # connect to bucket (CGP)
    gcp = Gcp()

    data_folder = config.project.get('bucket_data_folder')
    try:
        os.mkdir(data_folder)
    except OSError as error:
        pass

    model_folder = config.project.get('bucket_models_folder')
    try:
        os.mkdir(model_folder)
    except OSError as error:
        pass

    if args[0] == 'data_collection':
        print(data_collection(gcp, config))

        exit(0)

    elif args[0] == 'get_all_data':
        print(get_all_data(gcp, config))

        exit(0)
