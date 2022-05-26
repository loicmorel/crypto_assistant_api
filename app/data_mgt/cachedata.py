import os.path
import pandas as pd
from datetime import datetime
from app.config import Config
from app.data_mgt.gcpmgt import Gcp
from os import listdir
from os.path import isfile, join
from app.data_mgt import cachedata

def cache_pred(date, y_pred, model_name, symbol, frequency):

    # print('cache:', date, y_pred, model_name, symbol, frequency)

    file_path = search_model_offline(model_name, symbol, frequency)

    add_row = {}
    if os.path.isfile(file_path):
        df = pd.read_csv(file_path)
    else:
        df = pd.DataFrame(columns=['date', 'y_pred'], dtype=object)

    add_row['date'] = date
    add_row['y_pred'] = y_pred
    df = pd.concat([df, pd.DataFrame([add_row])], axis=0, ignore_index=True)
    df.to_csv(file_path, index=False)


def load_cached_pred(date, model_name, symbol, frequency):

    # print('load cache:', date, model_name, symbol, frequency)

    file_path = search_model_offline(model_name, symbol, frequency)

    if os.path.isfile(file_path):
        df = pd.read_csv(file_path)[::-1]
        y_pred = df[df['date']==str(date)]['y_pred']
        if len(y_pred) > 0:
            y_pred.values[0]
            return y_pred.values[0]
    return 'null'

def search_model_offline(model_name, symbol, frequency):
    model_folder = Config().project.get('bucket_models_folder')

    # search offline
    files = [f for f in listdir(model_folder) if isfile(join(model_folder, f))]

    available_files = []
    for file in files:
        if model_name in file and symbol in file and \
            frequency in file and 'h5' in file:
            available_files.append(file)
    if len(available_files) == 0:
        print('model not found for:',
            model_name, symbol, frequency)
        return 'null'
    file = sorted([file for file in available_files])[-1]

    if file == 'null':
        return 'null'
    file_path = f'{model_folder}/{os.path.splitext(file)[0]+".cache"}'
    return file_path

if __name__ == "__main__":

    from datetime import timedelta

    date = datetime.strptime("2022-05-11_00:00:00", "%Y-%m-%d_%H:%M:%S")
    y_pred = 10

    # cache_pred(date + timedelta(days=1), y_pred+1, 'CNN', 'ETHUSDT', '1h')
    # cache_pred(date + timedelta(days=3), y_pred+2, 'CNN', 'ETHUSDT', '1h')
    # cache_pred(date + timedelta(days=3), y_pred+3, 'CNN', 'ETHUSDT', '1h')
    # cache_pred(date + timedelta(days=4), y_pred+4, 'CNN', 'ETHUSDT', '1h')

    print('load cache:', load_cached_pred(date + timedelta(days=0), 'CNN', 'ETHUSDT', '1h'))
