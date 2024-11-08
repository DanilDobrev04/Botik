# conditions.py

def check_long_condition(macd, macdsignal, adx, obv_trend):
    # Условия для лонга: MACD пересекает сигнал снизу вверх, ADX > 20, OBV показывает восходящий тренд
    return macd[-1] > macdsignal[-1] and adx[-1] > 20 and obv_trend == "up"

def check_short_condition(macd, macdsignal, adx, obv_trend):
    # Условия для шорта: MACD пересекает сигнал сверху вниз, ADX > 20, OBV показывает нисходящий тренд
    return macd[-1] < macdsignal[-1] and adx[-1] > 20 and obv_trend == "down"
