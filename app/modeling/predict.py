
from app.modeling.model_RNN import RNNModel
from app.modeling.model_CNN import CNNModel
from app.data_mgt.cachedata import load_cached_pred
from app.data_mgt.cachedata import cache_pred
from app.modeling.utils import adding_target_to_data
from os import listdir
from os.path import isfile, join
import pandas as pd

def CNN_model_prediction(metadata, data, date):

    if date > pd.to_datetime(metadata['end_ts'], unit='ms'):
        print('Error: date not existing in the data', date)
        return -1

    CNN_model_params = {
        'model_name':'CNN',
        # data for training
        'metadata': metadata,

        # Depth of the timeframe, higher depth = bigger image.
        'depth': 40,
        # always 4x different frequency to constitute the 2x2 matrix of GAF images
        'freq': ['1h', '2h', '4h', '1d'],
        # focus on the Close price
        'focus': ['Close'],
        # sensitive to targets LL and HH
        'target': ['LL','HL','HH','LH','NP'],
    }

    ## check cached  predictions
    y_pred_cache = load_cached_pred(date,
                    CNN_model_params['model_name'],
                    CNN_model_params['metadata']['symbol'],
                    CNN_model_params['metadata']['frequency'])
    if y_pred_cache != 'null':
        print('prediction (cached):', metadata.get('symbol'), date, y_pred_cache)
        return y_pred_cache

    #print('not found in cache...')

    ## Targets definition (merge to data df)
    data = adding_target_to_data(data)

    cnn = CNNModel(CNN_model_params)
    if cnn.model_loading():
        y_pred = cnn.model_prediction(date, data)
        # cache prediction
        cache_pred(date, y_pred,
                   CNN_model_params['model_name'],
                   CNN_model_params['metadata']['symbol'],
                   CNN_model_params['metadata']['frequency'])
        print('prediction:', metadata.get('symbol'), date, y_pred)
        return y_pred
    else:
        return -1

def RNN_model_prediction(metadata, data, date):

    if date > pd.to_datetime(metadata['end_ts'], unit='ms'):
        print('Error: date not existingint he data', date)
        return -1

    RNN_model_params = {
        'model_name':'RNN',
        # data for training
        'metadata': metadata,
        # model parameters
        'labels': {0:'LL',1:'HL',2:'HH',3:'LH',4:'NP'}
    }

    ## check cached  predictions
    y_pred_cache = load_cached_pred(date,
                    RNN_model_params['model_name'],
                    RNN_model_params['metadata']['symbol'],
                    RNN_model_params['metadata']['frequency'])
    if y_pred_cache != 'null':
        print('prediction:', metadata.get('symbol'), date, y_pred)
        return y_pred_cache

    #print('not found in cache...')

    ## Targets definition (merge to data df)
    data = adding_target_to_data(data)

    rnn = RNNModel(RNN_model_params)
    if rnn.model_loading():
        y_pred = rnn.model_prediction(date, data)
        # cache prediction
        cache_pred(date, y_pred,
                   RNN_model_params['model_name'],
                   RNN_model_params['metadata']['symbol'],
                   RNN_model_params['metadata']['frequency'])
        print('prediction:', metadata.get('symbol'), date, y_pred_cache)
        return y_pred
    else:
        return -1

if __name__ == "__main__":
    from datetime import datetime
    from app.data_mgt.datamgt import ohlcv_from_csv_to_df
    from datetime import timedelta
    from app.config import Config

    data_folder = Config().project.get('bucket_data_folder')

    ######## Models prediction ########

    predict_date = datetime.strptime("2022-05-11_00:00:00", "%Y-%m-%d_%H:%M:%S")

    data_paths = [f for f in listdir(f'{data_folder}/') if isfile(join(f'{data_folder}/', f))]

    for data_path in data_paths:

        list_of_metadata = data_path.split('_')
        metadata = {
            'symbol' : list_of_metadata[1],
            'frequency' : list_of_metadata[2],
            'start_ts' : list_of_metadata[4],
            'end_ts' : list_of_metadata[6].rsplit( ".", 1 )[0]
        }

        if metadata['frequency'] == '1h' and metadata['frequency'] == 'ETH':

            ## Data collection
            data = ohlcv_from_csv_to_df(f'{data_folder}/{data_path}')

            for i in range(0,20):

                y_date = predict_date + timedelta(days=i)

                print(
                    metadata.get('symbol'),
                    y_date,
                    RNN_model_prediction(metadata, data, y_date)
                )

                print(
                    metadata.get('symbol'),
                    y_date,
                    CNN_model_prediction(metadata, data, y_date)
                )

                #exit(0)
