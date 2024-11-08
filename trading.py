# trading.py

from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET, ORDER_TYPE_LIMIT
import config
import logging

client = Client(config.api_key, config.api_secret, testnet=config.testnet)


def get_klines(symbol, interval):
    try:
        candles = client.futures_klines(symbol=symbol, interval=interval)

        # Извлечение значений high, low, close, volume
        closes = [float(candle[4]) for candle in candles]
        volumes = [float(candle[5]) for candle in candles]
        highs = [float(candle[2]) for candle in candles]
        lows = [float(candle[3]) for candle in candles]

        return closes, volumes, highs, lows
    except Exception as e:
        logging.error(f"Error fetching klines for {symbol} with interval {interval}: {e}")
        return [], [], [], []

# Получение данных о точности для символа
def get_symbol_precision(symbol):
    exchange_info = client.futures_exchange_info()
    for s in exchange_info['symbols']:
        if s['symbol'] == symbol:
            quantity_precision = s['quantityPrecision']
            price_precision = s['pricePrecision']
            return quantity_precision, price_precision
    return None, None


# trading.py

def get_tick_size(symbol):
    """Получает минимальный шаг изменения цены (tick size) для символа."""
    try:
        info = client.futures_exchange_info()
        for s in info['symbols']:
            if s['symbol'] == symbol:
                for f in s['filters']:
                    if f['filterType'] == 'PRICE_FILTER':
                        return float(f['tickSize'])
    except Exception as e:
        logging.error(f"Failed to get tick size for {symbol}: {e}")
    return 0.01  # Возвращаем безопасное значение по умолчанию, если запрос не удался


# trading.py

def place_order_with_sl_tp(symbol, side, quantity, entry_price, atr):
    # Пример расчета уровней стоп-лосса и тейк-профита
    if side == SIDE_BUY:
        take_profit = entry_price - (2 * atr)  # Пример для лонга
        stop_loss = entry_price + (1.5 * atr)  # Стоп-лосс выше входа
    elif side == SIDE_SELL:
        take_profit = entry_price + (2 * atr)  # Пример для шорта
        stop_loss = entry_price - (1.5 * atr)  # Стоп-лосс ниже входа

    # Размещение ордера с тейк-профитом и стоп-лоссом
    order = client.futures_create_order(
        symbol=symbol,
        side=side,
        type='MARKET',
        quantity=quantity
    )

    # Установка тейк-профита и стоп-лосса
    client.futures_create_order(
        symbol=symbol,
        side=side,
        type='TAKE_PROFIT_MARKET',
        quantity=quantity,
        stopPrice=take_profit
    )

    client.futures_create_order(
        symbol=symbol,
        side=side,
        type='STOP_MARKET',
        quantity=quantity,
        stopPrice=stop_loss
    )

    return order


def calculate_quantity(symbol, entry_value, leverage):
    try:
        # Получаем текущую рыночную цену символа
        ticker = client.futures_symbol_ticker(symbol=symbol)
        current_price = float(ticker['price'])

        # Рассчитываем итоговую сумму позиции с учетом кредитного плеча
        notional_value = entry_value * leverage

        # Рассчитываем количество (quantity) исходя из итоговой суммы
        quantity = notional_value / current_price
        return round(quantity, 6)  # Округляем до 6 знаков для точности
    except Exception as e:
        logging.error(f"Error calculating quantity for {symbol}: {e}")
        return 0

# trading.py

# trading.py

def check_open_position(symbol):
    try:
        position_info = client.futures_position_information(symbol=symbol)
        if not position_info or len(position_info) == 0:
            logging.info(f"No position information returned for {symbol}. Assuming no active position.")
            return False
        position = float(position_info[0]['positionAmt'])
        return position != 0  # True, если есть активная позиция
    except Exception as e:
        logging.error(f"Error checking open position for {symbol}: {e}")
        return False


def get_balance():
    try:
        balance_info = client.futures_account_balance()
        for balance in balance_info:
            if balance['asset'] == 'USDT':  # Предполагаем, что счет в USDT
                return float(balance['balance'])
    except Exception as e:
        logging.error(f"Failed to fetch balance: {e}")
    return 0.0  # Возвращаем 0.0, если не удалось получить баланс
