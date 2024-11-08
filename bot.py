# bot.py
import time
import logging
from indicators import calculate_macd, calculate_adx, calculate_obv, calculate_atr
from conditions import check_long_condition, check_short_condition
from trading import get_klines, place_order_with_sl_tp, get_balance, client, calculate_quantity, check_open_position
from binance.enums import SIDE_BUY, SIDE_SELL
import config

logging.basicConfig(filename='trade_logs.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Глобальные переменные для отслеживания прибыли и убытка
total_profit = 0.0
total_loss = 0.0

def update_profit_and_loss(symbol, position_side):
    global total_profit, total_loss
    try:
        # Получаем информацию о всех позициях
        closed_position_info = client.futures_position_information(symbol=symbol)
        for pos in closed_position_info:
            # Проверяем, закрыта ли позиция
            if pos['positionSide'] == position_side and float(pos['positionAmt']) == 0:  # Позиция закрыта
                # Получаем realized profit (только для закрытых сделок)
                pnl = float(pos['realizedProfit'])  # Используем realizedProfit
                if pnl > 0:
                    total_profit += pnl
                else:
                    total_loss += abs(pnl)
                logging.info(
                    f"Closed position for {symbol} | PnL: {pnl} | Total Profit: {total_profit} | Total Loss: {total_loss}")
                return  # Выходим из функции после обработки позиции
    except Exception as e:
        logging.error(f"Failed to update profit/loss for {symbol}: {e}")


def run_bot():
    logging.info("Bot started.")

    # Устанавливаем кредитное плечо для каждого символа в списке
    for symbol in config.symbol:
        try:
            client.futures_change_leverage(symbol=symbol, leverage=config.leverage)
            logging.info(f"Leverage set to {config.leverage}x for {symbol}")
        except Exception as e:
            logging.error(f"Failed to set leverage for {symbol}: {e}")

    while True:
        current_balance = get_balance()
        logging.info(
            f"Current Balance: {current_balance} USDT | Total Profit: {total_profit} | Total Loss: {total_loss}")

        for symbol in config.symbol:
            logging.info(f"Checking symbol {symbol}...")

            # Проверяем, если баланс меньше, чем entry_value, пропускаем открытие новых сделок
            if current_balance < config.entry_value:
                logging.warning(
                    f"Insufficient funds to open new position for {symbol}. Waiting for balance to increase or for trades to close.")
                continue

            if check_open_position(symbol):
                logging.info(f"Active position detected for {symbol}. Monitoring the market...")
                update_profit_and_loss(symbol, 'BOTH')  # Обновляем прибыль и убыток
                continue  # Пропускаем символ, если уже есть открытая позиция

            logging.info(f"No active position for {symbol}. Checking entry conditions...")
            closes, volumes, highs, lows = get_klines(symbol, config.timeframe)

            if not closes or not volumes or all(v == 0 for v in volumes):
                logging.error(f"No valid data received for klines or volume is zero for {symbol}.")
                continue

            logging.info("Calculating indicators...")

            macd, macdsignal = calculate_macd(closes)
            adx = calculate_adx(highs, lows, closes)
            obv = calculate_obv(closes, volumes)
            atr = calculate_atr(highs, lows, closes)[-1]

            obv_trend = "up" if obv[-1] > obv[-2] else "down"
            logging.info(
                f"{symbol} - MACD: {macd[-1]}, Signal: {macdsignal[-1]}, ADX: {adx[-1]}, OBV trend: {obv_trend}")

            quantity = calculate_quantity(symbol, config.entry_value, config.leverage)
            entry_price = closes[-1]

            # Проверяем условия для открытия длинной позиции
            if check_long_condition(macd, macdsignal, adx, obv_trend):
                logging.info(f"Long condition met for {symbol}.")
                order = place_order_with_sl_tp(symbol, SIDE_BUY, quantity, entry_price, atr)
                if order:
                    logging.info(f"Long position opened with TP/SL for {symbol}.")
                else:
                    logging.error(f"Failed to place long order with TP/SL for {symbol}.")

            # Проверяем условия для открытия короткой позиции
            elif check_short_condition(macd, macdsignal, adx, obv_trend):
                logging.info(f"Short condition met for {symbol}.")
                order = place_order_with_sl_tp(symbol, SIDE_SELL, quantity, entry_price, atr)
                if order:
                    logging.info(f"Short position opened with TP/SL for {symbol}.")
                else:
                    logging.error(f"Failed to place short order with TP/SL for {symbol}.")

        # Даем небольшой тайм-аут перед следующим проходом по всем символам
        time.sleep(300)


if __name__ == "__main__":
    run_bot()
