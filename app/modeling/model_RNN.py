import numpy as np
from app.modeling.utils import split_subsample_sequence
from tensorflow.keras import models
from tensorflow.keras import layers
from tensorflow.keras import optimizers
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import normalize
from app.data_mgt.gcpmgt import Gcp
from app.config import Config
from app.modeling.mlflow_tooling import Mlflow

class RNNModel():
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

        X, y = self._get_X_y(self.data, 2000, 21)

        len_ = int(0.8*self.data.shape[0])
        data_train = self.data[:len_]
        data_test = self.data[len_:]

        self.X_train, self.y_train = self._get_X_y(data_train, 2000, 21)
        self.X_test, self.y_test = self._get_X_y(data_test, 400, 21)

        # self.X_train=normalize(self.X_train)
        # self.X_test=normalize(self.X_test)
        # print(data_train)
        # exit(0)


    def model_compile(self):
        opt = optimizers.RMSprop(learning_rate=self.params['lr'])


        # normalizer = layers.LayerNormalization(axis=1)
        # normalizer.build(input_shape=self.X_train[0].shape)
        # normalizer = layers.experimental.preprocessing.Normalization()
        # normalizer.adapt(self.X_train)

        self.model = models.Sequential()
        # self.model.add(normalizer)
        self.model.add(layers.GRU(units=20, activation='tanh', return_sequences=True,input_shape=self.X_train[0].shape))
        self.model.add(layers.GRU(units=20, activation='tanh', return_sequences=False))
        self.model.add(layers.Dense(50, activation='relu'))
        self.model.add(layers.Dropout(0.3))
        self.model.add(layers.Dense(self.params['classes'], activation='softmax'))

        self.model.compile(loss='categorical_crossentropy',
                    optimizer=opt,
                    metrics=['accuracy'])

        print(self.model.summary())

    def model_fitting(self):
        class_weight = {
            0: 5.,
            1: 5.,
            2: 5.,
            3: 5.,
            4: 1.
        }
        self.model.fit(
            self.X_train,
            self.y_train,
            epochs=self.params['epochs'],
            batch_size=self.params['batch_size'],
            verbose=1,
            callbacks = [EarlyStopping(monitor='accuracy', patience=10)],
            validation_split=0.2,
            class_weight=class_weight
        )

        loss, accuracy = self.model.evaluate(self.X_test, self.y_test)
        print('loss:', loss, 'accuracy:', accuracy)

        # log to MLFlow
        self._track_on_mlf()
        self.mlf_client.log_param("name", self.params['model_name'])
        self.mlf_client.log_param("symbol", self.params['metadata']['symbol'])
        self.mlf_client.log_param("classes", self.params['classes'])
        self.mlf_client.log_param("lr", self.params['lr'])
        self.mlf_client.log_param("epochs", self.params['epochs'])
        self.mlf_client.log_param("batch_size", self.params['batch_size'])

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

        row_num = self._idx_from_dt(data, date_dt)
        #print('row matching the date:', row_num, date_dt)
        index_slices=range(row_num-19, row_num+1)
        X=data.loc[index_slices]
        X=X.drop(columns='o_ts')
        X_3d=np.array([X])

        pred=np.argmax(self.model.predict(X_3d))

        return self.params.get('labels').get(pred)

    def _get_X_y(self, df, n_sequences, length):
        '''Return a list of samples (X, y)'''
        X, y = [], []

        for i in range(n_sequences):
            (xi, yi) = split_subsample_sequence(df, length)
            X.append(xi)
            y.append(yi)

        X = np.array(X)
        y = np.array(y)
        return X, y

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
