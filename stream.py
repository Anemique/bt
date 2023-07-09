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
    global sell_order_placed, order, buying_price, buy_order_placed, bought, levels, close, high, low
    global closes, highs, lows, support, resistance, sell_price, sup_counter, buy_balance, balance, sell_quantity, sell_price_order
    global initial_balance, profit, balance_change

    if msg['e'] == 'error':
        print(f"Error: {msg['m']}")
    else:
        btc_price = float(msg['c'])

        if levels:
            sup_counter = sup_counter + 1
            if sup_counter > 60*5 and not bought and not buy_order_placed:
                levels = False
                sup_counter = 0

            if not bought:
                if not buy_order_placed:
                    if btc_price <= sell_price - 3 and btc_price > support + 10 and btc_price < resistance:
                        sell_price_order = btc_price
                        sell_quantity = 0.01500
                        buy_balance = sell_quantity * sell_price_order
                        balance = round(balance - buy_balance, 2)
                        order = orders.orderBuy(sell_quantity, sell_price_order, order, client)
                        buy_order_placed = True
                        telegramSend('buy_placing', {'sell_price': sell_price_order, 'sell_quantity': sell_quantity, 'buy_balance' : buy_balance})
                else:
                    if orders.checkOrder(client, order['orderId']):
                        bought = True
                        buy_order_placed = False

                        telegramSend('buy_filled')

                        order = orders.orderSell(sell_quantity, sell_price_order + 1, order, client)
                        sell_order_placed = True

                        telegramSend('sell_placing', {'sell_price': sell_price_order + 1, 'sell_quantity': sell_quantity})
            else:
                if orders.checkOrder(client, order['orderId']):
                    sell_order_placed = False
                    bought = False

                    profit = round((buy_balance / sell_price_order) * (sell_price_order + 1) - buy_balance, 2)
                    balance = balance + round(buy_balance + profit, 2)
                    balance_change = round(balance * 84 - initial_balance * 84, 2)

                    telegramSend('sell_filled', {'profit': profit, 'balance': '', 'balance_change': balance_change})

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
