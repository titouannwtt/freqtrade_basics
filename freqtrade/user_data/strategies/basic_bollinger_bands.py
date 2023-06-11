from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from typing import Optional, Union, Dict

#Nom de la stratégie
class basic_bb(IStrategy):

    #Takeprofit évolutif 
    #au bout de X minutes le takeprofit sera à VALEUR
    #(valeur entre 1.0 et 0.0 (pour définir entre 100% à 0%))
    minimal_roi = {
        "0": 0.63,
        "30000": 0.49,
        "50000": 0.42,
        "80000": 0
    }

    #Stoploss
    #(valeur entre 1.0 et 0.0 (pour définir entre 100% à 0%))
    stoploss = -0.35

    #Timeframe par défaut pour la stratégie
    timeframe = '1d'

    #Génération des indicateurs
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        #Génération de l'indicateur Bandes de Bollingers
        boll = ta.BBANDS(dataframe, nbdevup=2.1, nbdevdn=1.7, timeperiod=30)
        dataframe['bb_lower'] = boll['lowerband']
        dataframe['bb_middle'] = boll['middleband']
        dataframe['bb_upper'] = boll['upperband']
        dataframe[f"bb_width"] = (
            (dataframe[f"bb_upper"] - dataframe[f"bb_lower"]) / dataframe[f"bb_middle"]
        )

        #Génération de l'indicateur MACD
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']

        return dataframe

    #Condition d'ouverture d'une position (achat)
    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                    (dataframe['close'] > dataframe['bb_upper']) 
                    & (dataframe['bb_width'] > 0.045) 
            ),
            'buy'] = 1
        return dataframe

    #Condition de fermeture d'une position (vente)
    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                    (dataframe['macdsignal'] < 0)
            ),
            'sell'] = 1
        return dataframe


    #Permet d'obtenir les indicateurs graphiquement lors d'un plot-dataframe
    @property
    def plot_config(self):
        return {
            'main_plot': {
                'bb_upper': {'color': 'green'},
                'bb_middle': {'color': 'orange'},
                'bb_lower': {'color': 'red'},
            },
            'subplots': {
                "Bollinger Bands size": {
                    'bb_width': {'color': 'blue'}
                },
                "MACD": {
                    'macd': {'color': 'red'},
                    'macdsignal': {'color': 'blue'},
                }
            }
        }
