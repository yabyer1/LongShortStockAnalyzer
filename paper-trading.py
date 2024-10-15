import alpaca_trade_api as tradeapi
import backtrader as bt
from datetime import datetime

# Alpaca credentials
API_KEY = 'PKDY7NQ18NBZ59EDXB3C'
SECRET_KEY = 'bD0DFINEX1m0y6GRFhAhIi8x8iBzX6M8IIL0QEOq'
BASE_URL = 'https://paper-api.alpaca.markets'

# Connect to Alpaca API
alpaca = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')

# Function to fetch real-time data using Alpaca's API (5-minute interval example)
def get_real_time_data(symbol):
    try:
        bars = alpaca.get_barset(symbol, '5Min', limit=1)  # Fetch the latest 5-minute bar
        return bars[symbol][0]
    except Exception as e:
        print(f"Error fetching real-time data: {e}")
        return None

# Custom Strategy for Alpaca live trading
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
    
    def log(self, text):
        ''' Logging function for strategy '''
        print(f'{self.datas[0].datetime.date(0)}: {text}')

    def next(self):
        # Real-time data fetching from Alpaca (optional if not using backtrader's data)
        live_data = get_real_time_data('AAPL')
        if live_data:
            self.log(f"Live Data - Close Price: {live_data.c}")

        # Buy signal based on moving averages, RSI, and Bollinger Bands
        if self.ma50 > self.ma200 or self.rsi < self.params.rsi_oversold or self.data.close < self.bollinger.lines.bot:
            self.log(f"Buy Signal Triggered - Price: {self.data.close[0]}")
            self.buy_signal('AAPL', 10)  # Trigger live buy order on Alpaca

        # Sell signal
        if self.position and self.ma50 < self.ma200 and self.rsi > self.params.rsi_overbought and self.data.close > self.bollinger.lines.top:
            self.log(f"Sell Signal Triggered - Price: {self.data.close[0]}")
            self.sell_signal('AAPL', 10)  # Trigger live sell order on Alpaca

    def buy_signal(self, symbol, qty):
        ''' Alpaca API call to place a buy order '''
        try:
            alpaca.submit_order(
                symbol=symbol,
                qty=qty,
                side='buy',
                type='market',
                time_in_force='day'
            )
            self.log(f"Live Buy Order Placed: {qty} shares of {symbol}")
        except Exception as e:
            self.log(f"Error placing buy order: {e}")

    def sell_signal(self, symbol, qty):
        ''' Alpaca API call to place a sell order '''
        try:
            alpaca.submit_order(
                symbol=symbol,
                qty=qty,
                side='sell',
                type='market',
                time_in_force='day'
            )
            self.log(f"Live Sell Order Placed: {qty} shares of {symbol}")
        except Exception as e:
            self.log(f"Error placing sell order: {e}")

# Live Trading Setup
if __name__ == '__main__':
    cerebro = bt.Cerebro()

    # Using Alpaca's market data for live trading (not backtesting historical data)
    class AlpacaLiveData(bt.feeds.DataBase):
        def _load(self):
            live_data = get_real_time_data('AAPL')
            if live_data:
                self.lines.datetime[0] = bt.date2num(datetime.now())
                self.lines.close[0] = live_data.c
                self.lines.open[0] = live_data.o
                self.lines.high[0] = live_data.h
                self.lines.low[0] = live_data.l
                self.lines.volume[0] = live_data.v
                return True
            else:
                return False

    # Add live data feed
    cerebro.adddata(AlpacaLiveData())

    # Add strategy
    cerebro.addstrategy(AlpacaStrategy)

    # Set initial capital
    cerebro.broker.set_cash(100000)

    # Print the starting portfolio value
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run the strategy live
    cerebro.run()

    # Print the final portfolio value
    print('Ending Portfolio Value: %.2f' % cerebro.broker.getvalue())

