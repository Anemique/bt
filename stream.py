import signal
import math
import json
import websocket
import time
import pandas as pd
from binance.websockets import BinanceSocketManager

import creds                # Конфиг
import orders               # Выставление ордеров
import init                 # Инстанс клиента
import technicals           # Техническая дребедень
from telegramApi import *   # Телеграм
from variables import *     # Переменные

client = init.get_spot_client()
bm = BinanceSocketManager(client)

def reconnect():
    # Функция для переподключения
    while True:
        try:
            bm.start()
            ws.run_forever()
        except Exception as e:
            # Обработка исключений при возникновении ошибок
            print("Error during reconnection:", e)
            # Задержка перед новой попыткой подключения
            time.sleep(5)

def on_message(ws, message):
    global closes, highs, lows, support, resistance, sup_counter, sell_price, levels
    data = json.loads(message)

    close = float(data['k']['c'])
    high = float(data['k']['h'])
    low = float(data['k']['l'])
    closes.append(close)
    highs.append(high)
    lows.append(low)
    if len(closes) > 300:
        closes.pop(0)
        highs.pop(0)
        lows.pop(0)
        df = pd.DataFrame({'Close': closes, 'High': highs, 'Low': lows})
        support = df['Low'].min()
        resistance = df['High'].max()
        levels = True
        sell_price = resistance - ((resistance - support) / 2)

def handle_message(msg):
    global sell_order_placed, order, buying_price, buy_order_placed, bought, levels, close, high, low, check_sell_order_counter, check_sell_order_flag, last_sell
    global closes, highs, lows, support, resistance, sell_price, sup_counter, buy_balance, balance, sell_quantity, sell_price_order, check_buy_order_counter, last_sell_counter
    global initial_balance, profit, balance_change, is_side, is_side_counter, rsi, rsi_counter, prev_price, sell_active_price, is_stop, stop_placing, when_stop_price

    if msg['e'] == 'error':
        print(f"Error: {msg['m']}")
    else:
        btc_price = float(msg['c'])
        if levels:
            if last_sell_counter >= 600 and not buy_order_placed:
                last_sell = 30000
                last_sell_counter = 0
            if last_sell == 30000:
                last_sell = btc_price + 10
            rsi_counter -= 1
            if rsi_counter == 0:
                rsi = technicals.rsi(creds.symbolRsi)
                rsi_counter = 60*60
            is_side_counter -= 1
            if is_side_counter == 0:
                is_side = technicals.isSide()
                is_side_counter = 60*15
            if not bought:
                if not buy_order_placed:
                    if btc_price <= last_sell - 10 and btc_price <= sell_price and btc_price > support + 1 and btc_price < resistance and is_side and rsi and prev_price < btc_price:
                        sell_price_order = btc_price
                        sell_quantity = 0.01500
                        buy_balance = sell_quantity * sell_price_order
                        balance = round(balance - buy_balance, 2)

                        order = orders.orderBuy(sell_quantity, sell_price_order, order, client)
                        buy_order_placed = True

                        telegramSend('buy_placing', {'sell_price': sell_price_order, 'sell_quantity': sell_quantity, 'buy_balance' : buy_balance})
                    else:
                        last_sell_counter = last_sell_counter + 1
                else:
                    if check_buy_order_counter < 600:
                        check_buy_order_counter = check_buy_order_counter + 1
                        if orders.checkOrder(client, order['orderId']):
                            bought = True
                            buy_order_placed = False
                            check_buy_order_counter = 0

                            telegramSend('buy_filled')

                            sell_active_price = sell_price_order + 20
                            last_sell = sell_price_order + 20

                            order = orders.orderSell(sell_quantity, sell_price_order + 20, order, client)
                            sell_order_placed = True

                            telegramSend('sell_placing', {'sell_price': sell_price_order + 20, 'sell_quantity': sell_quantity})
                    else:
                        if orders.cancelOrder(client, order['orderId']):
                            last_sell = 30000
                            check_buy_order_counter = 0
                            balance = round(balance + buy_balance, 2)
                            buy_order_placed = False
                            telegramSend('order_canceled')
            else:
                if check_sell_order_counter < 300 and check_sell_order_flag:
                    check_sell_order_counter = check_sell_order_counter + 1
                    if btc_price <= sell_active_price - 100 and not is_stop:
                        check_sell_order_counter = 0
                        if orders.cancelOrder(client, order['orderId']):
                            order = orders.orderSell(sell_quantity, btc_price, order, client)
                            when_stop_price = btc_price - 20
                            is_stop = True
                            stop_placing = True

                            telegramSend('sell_placing_stop', {'sell_price': btc_price, 'sell_quantity': sell_quantity})
                    if not stop_placing:
                        if orders.checkOrder(client, order['orderId']):
                            sell_order_placed = False
                            bought = False
                            check_sell_order_flag = True
                            check_sell_order_counter = 0

                            if is_stop:
                                 profit = round((buy_balance / sell_price_order) * (when_stop_price + 20) - buy_balance, 2)
                            else:
                                profit = round((buy_balance / sell_price_order) * (sell_price_order + 20) - buy_balance, 2)
                                
                            balance = balance + round(buy_balance + profit, 2)
                            balance_change = round(balance * 94 - initial_balance * 94, 2)

                            if is_stop:
                                is_stop = False
                                telegramSend('sell_filled_stop', {'profit': profit, 'balance': '', 'balance_change': balance_change})
                            else:
                                telegramSend('sell_filled', {'profit': profit, 'balance': '', 'balance_change': balance_change})
                else:
                    if check_sell_order_flag:
                        check_sell_order_flag = False

                    check_sell_order_counter = check_sell_order_counter - 1
                    if check_sell_order_counter == 0:
                        check_sell_order_counter = 299
                        check_sell_order_flag = True
        prev_price = btc_price
        if stop_placing:
            stop_placing = False

conn_key = bm.start_symbol_ticker_socket(creds.symbol, handle_message)

def signal_handler(signum, frame):
    print(f"Received signal {signum}. Exiting...")
    bm.close()
    exit(0)

signal.signal(signal.SIGTERM, signal_handler)

try:
    bm.start()
    ws = websocket.WebSocketApp(creds.url_levels,
                            on_message=on_message)

    ws.run_forever()
except KeyboardInterrupt:
    sys.exit()