from app.modeling.model_RNN import RNNModel
from app.modeling.model_CNN import CNNModel
from app.data_mgt.datamgt import ohlcv_from_csv_to_df
from app.modeling.utils import adding_target_to_data
from os import listdir
from os.path import isfile, join
from app.config import Config
from datetime import datetime, timedelta

def CNN_model_training(data, metadata):
    CNN_model_params = {
        'model_name': 'CNN',

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

        # model parameters
        'lr': 0.001,
        'epochs': 50,
        'batch_size': 32,
        'patience': 20
    }

    ## CNN Training
    cnn = CNNModel(CNN_model_params)
    cnn.X_y_construct(data)
    cnn.model_compile()
    cnn.model_fitting()
    cnn.model_saving()

    # test prediction
    # cnn.model_loading()
    # print(cnn.model_prediction(datetime.strptime("2022-05-10_07:00:00", "%Y-%m-%d_%H:%M:%S"), data))

    return cnn

def RNN_model_training(data, metadata):

    ## Params for modelling
    RNN_model_params = {
        'model_name':'RNN',
        # data for training
        'metadata': metadata,
        # model parameters
        'classes': 5,
        'lr': 0.01,
        'epochs': 10,
        'batch_size': 64,
    }

    ## RNN Training
    rnn = RNNModel(RNN_model_params)
    rnn.X_y_construct(data)
    rnn.model_compile()
    rnn.model_fitting()
    rnn.model_saving()

    return rnn

def TrainOnAllData():

    data_folder = Config().project.get('bucket_data_folder')

    data_paths = [f for f in listdir(f'{data_folder}/') if isfile(join(f'{data_folder}/', f))]
    #data_paths = ['ohlcv_ETHUSDT_1h_from_1557410400000_to_1652101200000.csv']
    #print(data_paths)

    for data_path in data_paths:

        list_of_metadata = data_path.split('_')
        metadata = {
            'symbol' : list_of_metadata[1],
            'frequency' : list_of_metadata[2],
            'start_ts' : list_of_metadata[4],
            'end_ts' : list_of_metadata[6].rsplit( ".", 1 )[0]
        }

        if metadata['frequency'] == '1h':# and metadata['symbol'] == 'ETHUSDT':

            ## Data collection
            data = ohlcv_from_csv_to_df(f'{data_folder}/{data_path}')

            ## Targets definition (merge to data df)
            data = adding_target_to_data(data)

            data_rnn = data.set_index('o_ts')
            ## Hack remove some data from the df
            data_cnn = data[-10000:-1].reset_index().drop(columns='index')

            ## 2. models trining
            #RNN_model_training(data_rnn, metadata)
            CNN_model_training(data_cnn, metadata)

if __name__ == "__main__":

    ######## Models training ########
    TrainOnAllData()
