# indicators.py
import talib as ta
import numpy as np

def calculate_rsi(closes, period=14):
    return ta.RSI(np.array(closes), timeperiod=period)

def calculate_macd(prices, fastperiod=12, slowperiod=26, signalperiod=9):
    macd, macdsignal, _ = ta.MACD(np.array(prices), fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
    return macd, macdsignal

def calculate_adx(highs, lows, closes, period=14):
    return ta.ADX(np.array(highs), np.array(lows), np.array(closes), timeperiod=period)

def calculate_obv(closes, volumes):
    return ta.OBV(np.array(closes), np.array(volumes))

def calculate_atr(highs, lows, closes, period=14):
    """
    Рассчитывает Average True Range (ATR) на основе high, low и close цен.
    Используется для установки динамических уровней стоп-лосса и тейк-профита.
    """
    return ta.ATR(np.array(highs), np.array(lows), np.array(closes), timeperiod=period)
