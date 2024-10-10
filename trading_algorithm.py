import yfinance as yf
import pandas as pd
import numpy as np
import backtrader as bt

# Function to download Apple stock data
def get_data(ticker):
    try:
        data = yf.download(ticker, start="2022-01-01", end="2022-12-31")
        if data.empty:
            print(f"No data found for {ticker}, skipping.")
        return data
    except Exception as e:
        print(f"Error downloading {ticker}: {e}")
        return None  # Return None if there's an issue

# Function to add custom indicators (SMA, RSI, Bollinger Bands)
def add_indicators(data):
    data['50_MA'] = calculate_sma(data, 50)
    data['200_MA'] = calculate_sma(data, 200)
    data['RSI'] = calculate_rsi(data, 14)
    data['BB_Upper'], data['BB_Middle'], data['BB_Lower'] = calculate_bollinger_bands(data, window=20, num_of_std=2)
    return data

# Custom implementation for SMA
def calculate_sma(data, window):
    return data['Close'].rolling(window=window).mean()

# Custom implementation for RSI
def calculate_rsi(data, period=14):
    delta = data['Close'].diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Custom implementation for Bollinger Bands
def calculate_bollinger_bands(data, window=20, num_of_std=2):
    sma = data['Close'].rolling(window=window).mean()
    rolling_std = data['Close'].rolling(window=window).std()

    upper_band = sma + (rolling_std * num_of_std)
    lower_band = sma - (rolling_std * num_of_std)

    return upper_band, sma, lower_band

# Create custom strategy
class MovingAverageRSIBollingerStrategy(bt.Strategy):
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
        if self.position:
        # Sell Signal: Only execute if we own shares
            if self.ma50 < self.ma200 and self.rsi > self.params.rsi_overbought and self.data.close > self.bollinger.lines.top:
                self.sell()

# Backtesting setup
if __name__ == '__main__':
    # Initialize Cerebro (backtrader engine)
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(30000)  # Starting capital
    
    # Download Apple data and add to Cerebro
    ticker = 'AAPL'
    data = get_data(ticker)
    if data is not None:
        data = bt.feeds.PandasData(dataname=add_indicators(data))
        cerebro.adddata(data, name=ticker)
    
    # Add strategy
    cerebro.addstrategy(MovingAverageRSIBollingerStrategy)
    
    # Run the backtest
    initial_portfolio_value = cerebro.broker.getvalue()
    cerebro.run()
    final_portfolio_value = cerebro.broker.getvalue()
    
    print(f"Initial Portfolio Value: ${initial_portfolio_value}")
    print(f"Final Portfolio Value: ${final_portfolio_value}")

    # Show final plot
    cerebro.plot()
