
"""interaction with Binance API
"""
from binance.client import Client
from app.utils import ohlcv_to_df

class Binance():

    def __init__(self, config):
        """Open connection with Binance platform.
        """
        self.config = config
        self.public_key = self.config.exchanges.get('binance').get('public_key')
        self.secret_key = self.config.exchanges.get('binance').get('secret_key')
        self.client = Client(self.public_key, self.secret_key)
        self.status = self.client.get_system_status()

    def get_status(self):
        if self.status['msg'] != "normal":
            return 'error'
        return 'success'

    def get_historical_data(self, symbol, freq, start_date, end_date):
        data = self.client.get_historical_klines(symbol, freq, start_date, end_date)
        return data
