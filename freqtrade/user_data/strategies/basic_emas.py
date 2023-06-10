from functools import reduce
from freqtrade.strategy import IStrategy
from freqtrade.strategy import CategoricalParameter, DecimalParameter, IntParameter
from pandas import DataFrame

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


class basic_emas(IStrategy):
    INTERFACE_VERSION: int = 3
    minimal_roi = {
        "0": 1.0,
        "10000": 0.40,
        "25000": 0.15,
        "50000": 0
    }

    stoploss = -0.35

    timeframe = '1d'

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['ema12'] = ta.EMA(dataframe, timeperiod=12)
        dataframe['ema80'] = ta.EMA(dataframe, timeperiod=80)
        #print(dataframe)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                qtpylib.crossed_above(dataframe[f'ema12'], dataframe[f'ema80']) &
                (dataframe['volume'] > 0)
            ),
            'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                qtpylib.crossed_above(dataframe[f'ema80'],dataframe[f'ema12']) &
                (dataframe['volume'] > 0)
            ),
            'exit_long'] = 1
        return dataframe
