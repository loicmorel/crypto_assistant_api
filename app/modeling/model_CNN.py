import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pyts.image import GramianAngularField
from mpl_toolkits.axes_grid1 import ImageGrid
from app.indicators import find_swings
from app.indicators import classify_swings
from app.data_mgt.gcpmgt import Gcp
from app.config import Config
from sklearn.metrics import confusion_matrix
from tensorflow.keras import models
from tensorflow.keras import layers
from tensorflow.keras import utils
from tensorflow.keras import optimizers, metrics
from tensorflow.keras.callbacks import EarlyStopping
from app.modeling.mlflow_tooling import Mlflow
from sklearn.model_selection import train_test_split

class CNNModel():
    def __init__(self, params):
        self.params = params
        self.gcp = Gcp()
        self.config = Config()

    def X_y_construct(self,data):
        self.data = data
        print('construction of X and y for',
              self.params['metadata']['symbol'],
              self.params['model_name'],
              self.params['metadata']['frequency'])

        self.data['gaf'] = data[::-1].apply(
            lambda r: self._generate_gaf_images_from_ohlc(
                self.data, self.params, r.name+1), axis=1
        )
        self.data = self.data.dropna().reset_index().drop(columns='index')

        X = []
        y = []

        for gaf_meta in self.data.gaf:
            X.append(gaf_meta['img'])
        X = np.array(X)
        y = self.data[self.params['target']]
        y = np.array(y)

        self.X_train, self.X_test, self.y_train, self.y_test = \
            train_test_split(X, y, test_size=0.33, random_state=42)

        print(self.X_train.shape, self.y_train.shape)

    def model_compile(self):
        self.model = models.Sequential()

        # Conv1
        self.model.add(layers.Conv2D(16, (4, 4), input_shape=self.X_train.shape[1:], padding='same', strides=(1, 1)))
        self.model.add(layers.Activation('sigmoid'))

        # Conv2
        self.model.add(layers.Conv2D(16, (4, 4), padding='same', strides=(1, 1)))
        self.model.add(layers.Activation('sigmoid'))

        # FC
        self.model.add(layers.Flatten())
        self.model.add(layers.Dense(128, activation='relu'))
        self.model.add(layers.Dropout(0.3))

        self.model.add(layers.Dense(self.y_train.shape[1],activation='softmax'))

        self.model.compile(
            loss='categorical_crossentropy',
            optimizer=optimizers.Adam(lr=self.params['lr']),
            metrics=['accuracy']
        )

        print(self.model.summary())

    def model_fitting(self):
        class_weight = {
            0: 6,
            1: 6,
            2: 6,
            3: 6,
            4: 1.
        }

        #es=EarlyStopping(monitor='accuracy', patience=self.params['patience'])

        self.hist = self.model.fit(
            x=self.X_train, y=self.y_train,
            validation_split=0.2,
            batch_size=self.params['batch_size'],
            epochs=self.params['epochs'],
            verbose=2,
            #callbacks = [es],
            class_weight=class_weight
        )

        loss, accuracy = self.model.evaluate(self.X_test, self.y_test)
        print('loss:', loss, 'accuracy:', accuracy)

        # log to MLFlow
        self._track_on_mlf()
        self.mlf_client.log_param("name", self.params['model_name'])
        self.mlf_client.log_param("symbol", self.params['metadata']['symbol'])
        self.mlf_client.log_param("lr", self.params['lr'])
        self.mlf_client.log_param("epochs", self.params['epochs'])
        self.mlf_client.log_param("batch_size", self.params['batch_size'])
        # self.mlf_client.log_param("patience", self.params['patience'])

        self.mlf_client.log_metric("loss", loss)
        self.mlf_client.log_metric("accuracy", accuracy)

    def model_saving(self):

        self.gcp.save_model(
            self.model,
            self.params['model_name'],
            self.params['metadata']['symbol'],
            self.params['metadata']['frequency'],
            self.params['metadata']['start_ts'],
            self.params['metadata']['end_ts'],
            keep_localy=False)

    def model_loading(self):
        self.model = self.gcp.load_model(
            self.params['model_name'],
            self.params['metadata']['symbol'],
            self.params['metadata']['frequency'],
            keep_localy=True)
        return self.model

    def model_prediction(self, date_dt, data):

        X_pred = self._generate_gaf_images_from_ohlc(
            data,
            self.params,
            self._idx_from_dt(data, date_dt)+1
        )

        if str(X_pred) == 'nan':
            print('Error: X data cannot be constructed for CNN model')
            return -1

        pred = np.argmax(self.model.predict(np.array([X_pred['img']])))
        return self.params['target'][pred]

    def _track_on_mlf(self, **kwargs):
        ## Adding MLFlow tracking ##
        self.mlf_client = Mlflow(
            self.config.project.get('mlflow_experiment_name'),
            self.config.project.get('mlflow_uri')
        )
        self.mlf_client.create_run()
        self.mlf_client.print_url()

    def _idx_from_dt(self, data, dt):
        for index in range(0, len(data)):
            if (index+1) >= len(data) and data['o_ts'][index] >= dt:
                return index
            elif (index+1) >= len(data):
                return -1
            elif data['o_ts'][index] <= dt and data['o_ts'][index+1] > dt:
                return index
        return -1

    def _generate_gaf(self, data):
        gadf = GramianAngularField(method='difference', image_size=data.shape[0])
        img = gadf.fit_transform(pd.DataFrame(data).T)[0]
        return img

    def _generate_gaf_images_from_ohlc(self, data, params, idx):
        ## slicing data from the bottom of the df (reverse the time)
        ## to the top from the index provided by the lambda function

        data_slice = data[:idx][['o_ts'] + params['focus'] + params['target']]
        img = []
        ret = params.copy()

        for t in params['target']:
            if data_slice.iloc[-1][t]:
                target = t
        ret['target'] = target

        ## for 4x frequency to compose the gaf matrix
        for freq in params['freq']:
            data_ = data_slice.groupby(pd.Grouper(key='o_ts', freq=freq)).mean().reset_index()
            data_ = data_.dropna()
            data__ = data_[::-1].reset_index().drop(columns='index')
            data___ = data__[:params['depth']]
            if data___.shape[0] < params['depth']:
                #print("data___.shape[0] < params['depth']:", data___.shape[0], params['depth'])
                return np.nan
            ret[f'start_time_{freq}'] = data___['o_ts'].iloc[0]
            ret[f'end_time_{freq}'] = data___['o_ts'].iloc[-1]
            img.append(self._generate_gaf(data___[params['focus']]))
        ret['img'] = np.array(img)
        return (ret)

    def _plot_gaf_image_matrix(self, img_np, target):
        image_matrix: tuple =(2, 2)
        fig = plt.figure(figsize=[img * 4 for img in image_matrix])
        plt.title(f'Target: {target}')
        grid = ImageGrid(fig,
                        111,
                        axes_pad=0,
                        nrows_ncols=image_matrix,
                        share_all=True,
                        )

        for ax, im in zip(grid, img_np):
            # Iterating over the grid returns the Axes.
            ax.set_xticks([])
            ax.set_yticks([])
            ax.imshow(im, cmap='rainbow', origin='lower')
