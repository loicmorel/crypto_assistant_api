from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.portfolio_manager.portfolio import Portfolio
from datetime import timedelta
import ast
from app.config import Config
from app.data_mgt.gcpmgt import Gcp
from app.utils import daterange
from app.data_mgt.datamgt import get_all_data
from app.data_mgt.datamgt import data_collection
from app.modeling.training import TrainOnAllData
from os import listdir
from os.path import isfile, join
from app.data_mgt.datamgt import ohlcv_from_csv_to_df
from app.modeling.predict import RNN_model_prediction
from app.modeling.predict import CNN_model_prediction

ca_api = FastAPI()

ca_api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

print('colleting all data from gcp... please, wait!')
print('get all data:', get_all_data(Gcp(), Config()))

@ca_api.get("/")
def api_index():
    return {"greeting": "Welcome to the crypto world!"}

@ca_api.get("/get_pf_random")
def api_get_pf_random(
    name,
    ps_init_assets_str,
    date_str,
    coins_alloc_str):

    date = datetime.strptime(date_str, "%Y-%m-%d_%H:%M:%S")
    coins_alloc = ast.literal_eval(coins_alloc_str)

    pf = Portfolio(name, int(ps_init_assets_str), list(coins_alloc.keys()))

    # 0 = model allocation, 1 = random allocation
    rand_pred = 1

    # generate the portfolio for the analysis period
    for date in daterange(date - timedelta(days=20), date):
        pf.set_allocation(coins_alloc, date, rand_pred)

    return {'portfolio_name': pf.name, 'portfolio': pf.portfolio.to_json(),
            'portfolio_status': pf.status}

@ca_api.get("/get_pf")
def api_get_pf(
    name,
    ps_init_assets_str,
    date_str,
    coins_alloc_str):

    date = datetime.strptime(date_str, "%Y-%m-%d_%H:%M:%S")
    coins_alloc = ast.literal_eval(coins_alloc_str)

    pf = Portfolio(name, int(ps_init_assets_str), list(coins_alloc.keys()))

    # 0 = model allocation, 1 = random allocation
    rand_pred = 0

    # generate the portfolio for the analysis period
    for date in daterange(date - timedelta(days=20), date):
        pf.set_allocation(coins_alloc, date, rand_pred)

    return {'portfolio_name': pf.name, 'portfolio': pf.portfolio.to_json(),
            'portfolio_status': pf.status}

@ca_api.get("/get_window_pf")
def api_get_window_pf(
    name,
    ps_init_assets_str,
    start_date_str,
    end_date_str,
    coins_alloc_str):

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d_%H:%M:%S")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d_%H:%M:%S")
    coins_alloc = ast.literal_eval(coins_alloc_str)

    pf = Portfolio(name, int(ps_init_assets_str), list(coins_alloc.keys()))

    # 0 = model allocation, 1 = random allocation
    rand_pred = 0

    # generate the portfolio for the analysis period
    for date in daterange(start_date, end_date):
        pf.set_allocation(coins_alloc, date, rand_pred)

    return {'portfolio_name': pf.name, 'portfolio': pf.portfolio.to_json(),
            'portfolio_status': pf.status}

@ca_api.get("/get_all_data")
def api_get_all_data():
    files = get_all_data(Gcp(), Config())
    return files

@ca_api.get("/data_collection")
def api_data_collection():
    files = data_collection(Gcp(), Config())
    return files

@ca_api.get("/train_all_models")
def api_train_all_models():
    TrainOnAllData()
    return 'finished training...'

@ca_api.get("/gen_cache")
def api_gen_cache(date_str):

    date = datetime.strptime(date_str, "%Y-%m-%d_%H:%M:%S")
    data_folder = Config().project.get('bucket_data_folder')
    data_paths = [f for f in listdir(f'{data_folder}/') if isfile(join(f'{data_folder}/', f))]

    for data_path in data_paths:

        list_of_metadata = data_path.split('_')
        metadata = {
            'symbol' : list_of_metadata[1],
            'frequency' : list_of_metadata[2],
            'start_ts' : list_of_metadata[4],
            'end_ts' : list_of_metadata[6].rsplit( ".", 1 )[0]
        }

        if metadata['frequency'] == '1h':
            ## Data collection
            data = ohlcv_from_csv_to_df(f'{data_folder}/{data_path}')

            for _date in daterange(date - timedelta(days=20), date):
                CNN_model_prediction(metadata, data, _date)

    return 'finished caching...'

@ca_api.get("/get_avalaible_coins")
def api_get_avalaible_coins():

    data_folder = Config().project.get('bucket_data_folder')
    data_paths = [f for f in listdir(f'{data_folder}/') if isfile(join(f'{data_folder}/', f))]

    avalaible_coins = []
    for data_path in data_paths:

        list_of_metadata = data_path.split('_')
        coin = list_of_metadata[1].replace('USDT', '')
        freq = list_of_metadata[2]
        if coin not in avalaible_coins:
            avalaible_coins.append(coin)

    print('get_avalaible_coins:', sorted(avalaible_coins))

    return {'avalaible_coins': sorted(avalaible_coins)}
