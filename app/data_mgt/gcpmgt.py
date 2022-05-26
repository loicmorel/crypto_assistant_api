from importlib.metadata import files
from google.cloud import storage
import os
from termcolor import colored
from datetime import datetime
from app.config import Config
import dill as pickle
from app.indicators import true_range
from os import listdir
from os.path import isfile, join
from tensorflow.keras import models

class Gcp():
    def __init__(self):
        self.client = storage.Client()
        self.config = Config()
        self.bucket_name = self.config.project.get('bucket_name')
        self.bucket = self.client.bucket(self.bucket_name)
        self.data_folder = self.config.project.get('bucket_data_folder')
        self.model_folder = self.config.project.get('bucket_models_folder')

        try:
            os.mkdir(self.data_folder)
        except OSError as error:
            pass

        try:
            os.mkdir(self.model_folder)
        except OSError as error:
            pass

    def save_data(self, local_file, keep_localy=True):

        blob = self.bucket.blob(f"{self.data_folder}/{os.path.basename(local_file)}")
        blob.upload_from_filename(f"{local_file}")
        print(colored(f"=> ✅ {local_file} uploaded successfully to bucket"\
            f"{self.bucket_name} inside {self.data_folder}", "green"))
        if keep_localy == False:
            #print(f'deleting model localy: {local_file}')
            os.remove(f"{local_file}")
        return local_file

    def load_data(self, file, local_dir):
        print(f"Uploading {file}...")
        blob = self.bucket.blob(f"{local_dir}/{file}")
        blob.download_to_filename(f"{local_dir}/{file}")
        print(colored(f"=> ✅ {file} download successfully from bucket"\
            f"{self.bucket_name} inside {local_dir}", "green"))

    def save_model(self, model, model_name, symbol, frequency,
                   start_ts, end_ts, keep_localy=True):
        local_file = f"model_{model_name}_{symbol}_{frequency}_{start_ts}_"\
                f"{end_ts}_{datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}.h5"
        print('saving file:', f"{self.model_folder}/{local_file}")
        model.save(f"{self.model_folder}/{local_file}")
        # with open(f"{self.model_folder}/{local_file}", 'wb') as file:
        #     pickle.dump(model, file)
        print(f"Uploading model to bucket {self.bucket_name}...")
        blob = self.bucket.blob(f"{self.model_folder}/{local_file}")
        blob.upload_from_filename(f"{self.model_folder}/{local_file}")
        print(colored(f"=> ✅ {local_file} uploaded successfully to bucket"\
           f" {self.bucket_name} inside {self.model_folder}", "green"))
        if keep_localy == False:
            #print(f'deleting model localy: {local_file}')
            os.remove(f"{self.model_folder}/{local_file}")
        return local_file

    def load_model(self, model_name, symbol, frequency, keep_localy=True):
        model_path = self.fing_model(model_name, symbol, frequency)
        if model_path == 'null':
            return
        local_file = os.path.basename(model_path)
        #print('selected model:', local_file)
        if not os.path.isfile(model_path):
            blob = self.bucket.blob(model_path)
            print(f"Downloading model from bucket {self.bucket_name}...")
            blob.download_to_filename(f"{self.model_folder}/{local_file}")
            print(colored(f"=> ✅ {local_file} download successfully from bucket"\
                        f"{self.bucket_name} inside {model_path}", "green"))
            print('file to loaded:', f"{self.model_folder}/{local_file}")
        model = models.load_model(f"{self.model_folder}/{local_file}")
        # with open(f"{self.model_folder}/{local_file}", 'rb') as file:
        #     model = pickle.load(file)
        if keep_localy == False:
            print(f'deleting model localy: {local_file}')
            os.remove(f"{self.model_folder}/{local_file}")
        return model

    def list_files(self, dir_path):
        blobs = self.bucket.list_blobs(prefix=dir_path)
        return [ blob.name for blob in blobs ]

    def delete_file(self, remote_file):
        if remote_file in self.list_files(self.data_folder):
            print('deleting file on CGS:', remote_file)
            blob = self.bucket.blob(f"{self.data_folder}/{os.path.basename(remote_file)}")
            blob.delete()

    def fing_model(self, model_name, symbol, frequency):

        # search models on the bucket
        files = self.list_files(f'{self.model_folder}')
        # print('avalable models on bucket:', files)

        available_files = []
        for file in files:
            if model_name in file and symbol in file and \
                frequency in file and 'h5' in file:
                available_files.append(file)
        if len(available_files) == 0:
            print('model not found for:',
                model_name, symbol, frequency)
            return 'null'
        return sorted([file for file in available_files])[-1]

if __name__ == '__main__':

    gcp = Gcp()

    model = gcp.load_model(
        'RNN',
        'ETHUSDT',
        '1h',
        keep_localy=True)

    # gcp.save_model(
    #     model,
    #     'CNN',
    #     'BTCUSDT',
    #     '1h',
    #     'xxx',
    #     'yyy',
    #     keep_localy=False)
