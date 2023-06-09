# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from typing import Optional, Union
import ta as clean_ta

from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IStrategy, IntParameter)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from scipy.spatial.distance import cosine


# This class is a sample. Feel free to customize it.
class slope_is_dope(IStrategy):
    INTERFACE_VERSION = 3

    can_short: bool = False

    minimal_roi = {
        "0": 0.6,
        "5000" : 0.5,
    }

    stoploss = -0.5

    # Trailing stoploss
    trailing_stop = True
    trailing_only_offset_is_reached = True
    trailing_stop_positive = 0.002
    trailing_stop_positive_offset = 0.261

    timeframe = '1h'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    # These values can be overridden in the config.
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30

    # Optional order type mapping.
    order_types = {
        'entry': 'limit',
        'exit': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force.
    order_time_in_force = {
        'entry': 'GTC',
        'exit': 'GTC'
    }

    plot_config = {
        'main_plot': {
            'fastMA': {"color": "red"},
            'slowMA': {'color': 'blue'},
        },
        'subplots': {
            "rsi": {'rsi': {'color': 'blue'}},
            "fast_slope": {'fast_slope': {'color': 'red'}, "slow_slope": {"color": "blue"}},
        },
    }

    def informative_pairs(self):
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=7)
        dataframe['marketMA'] = ta.SMA(dataframe, timeperiod=200)
        dataframe['fastMA'] = ta.SMA(dataframe, timeperiod=21)
        dataframe['slowMA'] = ta.SMA(dataframe, timeperiod=50)
        dataframe['entryMA'] = ta.SMA(dataframe, timeperiod=3)

        dataframe['sy1'] = dataframe['slowMA'].shift(+11)
        dataframe['sy2'] = dataframe['slowMA'].shift(+1)
        sx1 = 1
        sx2 = 11
        dataframe['sy'] = dataframe['sy2'] - dataframe['sy1']
        dataframe['sx'] = sx2 - sx1
        dataframe['slow_slope'] = dataframe['sy']/dataframe['sx']
        dataframe['fy1'] = dataframe['fastMA'].shift(+11)
        dataframe['fy2'] = dataframe['fastMA'].shift(+1)
        fx1 = 1
        fx2 = 11
        dataframe['fy'] = dataframe['fy2'] - dataframe['fy1']
        dataframe['fx'] = fx2 - fx1
        dataframe['fast_slope'] = dataframe['fy']/dataframe['fx']

        dataframe['last_lowest'] = dataframe['low'].rolling(10).min().shift(1)

        dataframe['TRIX'] = clean_ta.trend.ema_indicator(clean_ta.trend.ema_indicator(clean_ta.trend.ema_indicator(close=dataframe['close'], window=15), window=15), window=15)
        dataframe['TRIX_PCT'] = dataframe["TRIX"].pct_change()*100
        dataframe['TRIX_SIGNAL'] = clean_ta.trend.sma_indicator(dataframe['TRIX_PCT'], 22)
        dataframe['TRIX_HISTO'] = dataframe['TRIX_PCT'] - dataframe['TRIX_SIGNAL']
        
        #ADX
        ADX = clean_ta.trend.ADXIndicator(dataframe['high'], dataframe['low'], dataframe['close'], window=20)
        dataframe['ADX'] = ADX.adx()
        dataframe['ADX_NEG'] = ADX.adx_neg()
        dataframe['ADX_POS'] = ADX.adx_pos()
        dataframe['ADXV'] = dataframe['ADX_POS'] - dataframe['ADX_NEG']
        dataframe['EMA45']=clean_ta.trend.ema_indicator(close=dataframe['close'], window=45)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (
                    (dataframe['TRIX_HISTO'] >= -0.58) &
                    (dataframe['ADXV'] > 0.4) & 
                    (dataframe['close']*0.99 > dataframe['marketMA']) &
                    (dataframe['fast_slope'] > 0) &
                    (dataframe['slow_slope'] > 0) &
                    (dataframe['EMA45'] < dataframe['close']*0.995) & 
                    (dataframe['close']*0.9997 > dataframe['close'].shift(+11)) &
                    (dataframe['rsi'] > 55) &
                    (dataframe['fastMA']*1.5 > dataframe['slowMA'])
                )
            ),
            'enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['fastMA'] < dataframe['slowMA']*1.005)
                | (dataframe['close']*1.004 < dataframe['last_lowest'])
                & (dataframe['TRIX_HISTO'] >= -0.7) 
            ),

            'exit_long'] = 1
        return dataframe
