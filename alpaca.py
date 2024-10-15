import alpaca_trade_api as tradeapi
import backtrader as bt
import pandas as pd
from datetime import datetime
import requests
# Alpaca credentials
API_KEY = 'PKDY7NQ18NBZ59EDXB3C'
SECRET_KEY = 'bD0DFINEX1m0y6GRFhAhIi8x8iBzX6M8IIL0QEOq'
BASE_URL = 'https://paper-api.alpaca.markets'

# Connect to Alpaca API
alpaca = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')

# Function to fetch historical data using Alpaca's updated API
def get_historical_data(symbol, start, end):
    start = pd.Timestamp(start).strftime('%Y-%m-%d')
    end = pd.Timestamp(end).strftime('%Y-%m-%d')

    # Fetch historical bars data from the v2 API
    bars = alpaca.get_bars(symbol, '1Min', start=start, end=end).df
    return bars

# Custom Strategy Example (Moving Average Cross with RSI)
class AlpacaStrategy(bt.Strategy):
    params = (
        ('short_ma_period', 20),
        ('long_ma_period', 50),
        ('rsi_period', 14),
        ('rsi_overbought', 70),
        ('rsi_oversold', 30),
    )
    
    def __init__(self):
        self.ma50 = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.short_ma_period)
        self.ma200 = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.long_ma_period)
        self.rsi = bt.indicators.RelativeStrengthIndex(self.data.close, period=self.params.rsi_period)
        self.bollinger = bt.indicators.BollingerBands(self.data.close, period=20, devfactor=2)

    def next(self):
        # Buy Signal
        if self.ma50 > self.ma200 or self.rsi < self.params.rsi_oversold or self.data.close < self.bollinger.lines.bot:
            self.buy()
            sendBuySignal()
        if self.position:
        # Sell Signal: Only execute if we own shares
            if self.ma50 < self.ma200 and self.rsi > self.params.rsi_overbought and self.data.close > self.bollinger.lines.top:
                self.sell()
                sendSellSignal()

# Run the backtrader engine with Alpaca
def sendBuySignal():
    url = 'http://your-django-backend.com/api/trade/'
    data = {
        'symbol': 'AAPL',
        'action': 'buy',
        
      
    }

    response = requests.post(url, json=data)


def sendSellSignal():
    url = 'http://your-django-backend.com/api/trade/'
    data = {
        'symbol': 'AAPL',
        'action': 'sell',
        
        
    }

    response = requests.post(url, json=data)

if __name__ == '__main__':
    cerebro = bt.Cerebro()

    # Fetch historical data for AAPL
    start_date = '2022-01-01'
    end_date = '2022-12-31'
    df = get_historical_data('AAPL', start=start_date, end=end_date)

    # Pass the DataFrame to Backtrader
    data_feed = bt.feeds.PandasData(dataname=df)

    # Add data to Cerebro
    cerebro.adddata(data_feed)

    # Adding the strategy
    cerebro.addstrategy(AlpacaStrategy)

    # Setting initial cash
    cerebro.broker.set_cash(30000)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    # Start backtrader
    cerebro.run()

    print('Ending Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.plot()
