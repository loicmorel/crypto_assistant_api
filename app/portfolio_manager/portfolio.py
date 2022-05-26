import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from app.data_mgt.datamgt import ohlcv_from_csv_to_df
from app.modeling.predict import RNN_model_prediction
from app.modeling.predict import CNN_model_prediction
from app.modeling.utils import adding_target_to_data
from datetime import timedelta, date
from app.config import Config
import os
import random

class Portfolio():
    def __init__(self, name, init_assets, coins):
        self.name = name
        self.init_assets = init_assets
        self.coins = coins
        self.data_folder = Config().project.get('bucket_data_folder')
        self.portfolio = pd.DataFrame(columns=[
            'date',
            't_bh_alloc',
            't_bh_perf',
            't_bh_val',
            't_ai_alloc',
            't_ai_stable',
            't_ai_perf',
            't_ai_val'
        ], dtype=object)

        self.data_1h = {}
        self.data_1d = {}
        self.metadata = {}
        self.status = 'init'

        # for all coins in the coins dict
        for coin  in self.coins:

            # collecting data for the coin.
            if self._set_ohlcv_data(coin, '1d') == -1:
                self.status = f'no data found for {coin} @1d'
                return self.status

            if self._set_ohlcv_data(coin, '1h') == -1:
                self.status = f'no data found for {coin} @1h'
                return self.status

    def delete_protfolio(self):
        self.__init__


    def get_coins(self):
        return self.coins

    def set_allocation(self, coins_dict, date, rand_pred):

        add_row = {}
        # add row with current date
        add_row['date'] = date
        total_bh_alloc = total_bh_perf = total_bh_val = 0
        total_ai_alloc = total_ai_perf = total_ai_val = 0

        # colelct previous valuations
        if len(self.portfolio) > 1:
            p_t_bh_val = self.portfolio['t_bh_val'].iloc[-1]
            p_t_ai_val = self.portfolio['t_ai_val'].iloc[-1]
        else:
            p_t_bh_val = p_t_ai_val = self.init_assets

        # generate prediction for all coins ()
        ai_alloc_d = self._get_ai_alloc(coins_dict, date, rand_pred)
        if ai_alloc_d == -1:
            self.status = f'error prediction (data or model)'
            return self.status

        # for all coins in the coins dict
        for coin, alloc in coins_dict.items():

            # check if date in data
            if not self._check_date_in_data(coin, date):
                self.status = f'no date found in the dataset ohlcv for {coin}'
                return self.status

            # calculate performance
            perf = self._perf_calc(self.data_1d[coin], date)

            # calculate valuation
            val = self._valuation_calc(self.data_1d[coin], date)

            # add rows for buy and hold
            add_row[f'{coin}_bh_alloc'] = alloc
            add_row[f'{coin}_perf'] = perf
            add_row[f'{coin}_val'] = val
            add_row[f'{coin}_bh_nb'] = (p_t_bh_val * (alloc/100)) / val
            total_bh_alloc += alloc
            total_bh_perf += perf * (alloc/100)
            total_bh_val += (p_t_bh_val * (alloc/100))

            # add rows for predictions
            ai_alloc = ai_alloc_d.get(coin)
            add_row[f'{coin}_ai_alloc'] = ai_alloc
            add_row[f'{coin}_ai_nb'] = (p_t_ai_val * (ai_alloc/100)) / val
            total_ai_perf += perf * (ai_alloc/100)
            total_ai_val += (p_t_ai_val * (ai_alloc/100))

        # add totals for buy and hold
        add_row['t_bh_alloc'] = total_bh_alloc
        add_row['t_bh_perf'] = total_bh_perf
        add_row['t_bh_val'] = p_t_bh_val + (p_t_bh_val * total_bh_perf/100)

        # add totals for prediction
        add_row['t_ai_alloc'] = sum(ai_alloc_d.values())
        add_row['t_ai_perf'] = total_ai_perf
        add_row['t_ai_stable'] = 100 - add_row['t_ai_alloc']
        add_row['t_ai_val'] = p_t_ai_val + (p_t_ai_val * total_ai_perf/100 + add_row['t_ai_stable']/100)


        self.portfolio = pd.concat([self.portfolio, pd.DataFrame([add_row])], axis=0, ignore_index=True)
        self.portfolio = self.portfolio.fillna(0)
        self.status = 'ready'
        return self.status


    def _set_ohlcv_data(self, coin, freq):
        # list avalable data of frequency
        for f in os.listdir(self.data_folder):
            if f'{coin}USDT_{freq}' in f:
                data = ohlcv_from_csv_to_df(f'{self.data_folder}/{f}')

                if freq == '1d':
                    self.data_1d[coin] = data

                elif freq == '1h':
                    self.data_1h[coin] = data

                list_of_metadata = f.split('_')
                self.metadata[coin] = {
                    'symbol' : list_of_metadata[1],
                    'frequency' : list_of_metadata[2],
                    'start_ts' : list_of_metadata[4],
                    'end_ts' : list_of_metadata[6].rsplit( ".", 1 )[0]
                }
                return 0
        return -1

    def _perf_calc(self, data, date):
        p = data['Close'][(data['o_ts'] == date)].values[0]
        p_1 = data['Close'][(data['o_ts'] == (date - timedelta(days=1)))].values[0]
        return (p - p_1) / p_1 * 100

    def _valuation_calc(self, data, date):
        return (data['Close'][(data['o_ts'] == date)].values[0] +
                data['Open'][(data['o_ts'] == date)].values[0]) / 2

    def _check_date_in_data(self, coin, date):
        return len(self.data_1d[coin][self.data_1d[coin]['o_ts'] == date])

    def _get_ai_alloc(self, coins_dict, date, random):

        pred = {}

        if random == 0:
            #print('manage prediction and new allocation for:', coins_dict, date)

            total_value = 0

            for coin, alloc in coins_dict.items():
                #print('collect prediction for:', coin, date)

                metadata = self.metadata[coin]

                #y_pred = RNN_model_prediction(metadata, self.data_1h[coin], date)
                y_pred = CNN_model_prediction(metadata, self.data_1h[coin], date)

                #print('prediction:', metadata.get('symbol'), date, y_pred)

                if y_pred == -1:
                    return -1

                alloc_dict = {
                    'NP': +0,
                    'HH': -40,
                    'LL': +60,
                    'LH': -20,
                    'HL': +20
                }
                pred[coin] = coins_dict.get(coin) + alloc_dict.get(y_pred)
                if pred[coin] < 0:
                    pred[coin] = 0
                total_value += pred[coin]
                if pred[coin] < 0 or total_value < 0:
                    print('01. coin alloc:', pred[coin], 'total_value:', total_value)

            to_reallocate = 100 - total_value

            total_coins_alloc = 0
            if to_reallocate < 0:
                # we squize to 100%
                for coin, alloc in coins_dict.items():
                    pred[coin] = pred[coin] + to_reallocate * alloc/100
                    if pred[coin] < 0:
                        pred[coin] = 0
                    total_coins_alloc += pred[coin]
                    if pred[coin] < 0 or total_value < 0:
                        print('01. coin alloc:', pred[coin], 'total_value:', total_value)

            if sum(pred.values()) > 100:
                # print('Over 100%:', pred)
                for coin, alloc in coins_dict.items():
                    pred[coin] = pred[coin] + to_reallocate * alloc/100
                    if pred[coin] < 0:
                        pred[coin] = 0
                    total_coins_alloc += pred[coin]
                    if pred[coin] < 0 or total_value < 0:
                        print('03. coin alloc:', pred[coin], 'total_value:', total_value)

            if sum(pred.values()) > 100:
                print('Over 100%:', pred)

            #print('total_coins_alloc:', total_coins_alloc)

        else:
            rand_alloc = self._generate_random_values(len(coins_dict), 100)

            i = 0
            for coin, alloc in coins_dict.items():
                pred[coin] = np.array(rand_alloc).tolist()[i]
                i = i + 1

        return pred

    def _generate_random_values(self, nb_val, cap):
        ran_val = []
        for i in range(nb_val-1):
            ran_val.append(random.randrange(0, int(cap/3)))
        arr = np.array(ran_val)
        final_value = 100 - arr.sum()
        arr = np.append(arr, final_value)
        return arr


if __name__ == "__main__":
    from app.utils import daterange

    #### API ####

    # define the name
    pf_name = 'Loic'

    # define initial assets (USD)
    ps_init_assets = 1000

    # today
    date = datetime.strptime("2022-04-22_00:00:00", "%Y-%m-%d_%H:%M:%S")

    # define allocation dictionary
    coins_dict = {
        'ETH': 20,
        'VITE': 30,
        'BTC': 50
    }

    #############

    pf = Portfolio(pf_name, ps_init_assets, list(coins_dict.keys()))

    # 0 = model allocation, 1 = random allocation
    rand_pred = 0

    # generate the portfolio for the analysis period
    for date in daterange(date - timedelta(days=10), date):
        pf.set_allocation(coins_dict, date, 'data', rand_pred)

    print(pf.portfolio)
