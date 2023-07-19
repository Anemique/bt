import requests
import pandas as pd
import ta
import time
import ccxt

def isSide():
    # Определяем URL-адрес API для получения исторических данных пары BTC/USDT
    url = 'https://api.binance.com/api/v3/klines?symbol=BTCTUSD&interval=1h'

    # Отправляем GET-запрос на API
    response = requests.get(url)

    # Проверяем, успешно ли выполнен запрос
    if response.status_code == 200:
        # Преобразуем ответ в формат JSON и создаем DataFrame
        data = response.json()
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        
        # Преобразуем столбец с временными метками в формат datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Вычисляем полосы Боллинджера
        df['close'] = df['close'].astype(float)
        indicator_bb = ta.volatility.BollingerBands(df['close'], window=20)
        df['bb_upper'] = indicator_bb.bollinger_hband()
        df['bb_middle'] = indicator_bb.bollinger_mavg()
        df['bb_lower'] = indicator_bb.bollinger_lband()
        
        # Проверяем, находится ли цена внутри полос Боллинджера
        is_sideways = (df['close'] > df['bb_lower']) & (df['close'] < df['bb_upper'])
        
        # Проверяем, есть ли последний час бокового движения
        if is_sideways.iloc[-1]:
            return True
        else:
            return False
    else:
        print("Ошибка при выполнении запроса.")

# Функция для расчета RSI
def calculate_rsi(candles):
    # Инициализируем переменные
    gains = []
    losses = []
    prev_close = candles[0][4]

    # Проходим по всем свечам, начиная со второй
    for i in range(1, len(candles)):
        close = candles[i][4]
        diff = close - prev_close

        # Определяем, является ли изменение положительным или отрицательным
        if diff > 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))

        prev_close = close

    # Вычисляем среднее значение приростов и потерь
    avg_gain = sum(gains) / len(gains)
    avg_loss = sum(losses) / len(losses)

    # Вычисляем относительную силу (RS)
    rs = avg_gain / avg_loss

    # Вычисляем RSI
    rsi = 100 - (100 / (1 + rs))

    return rsi

def rsi(symbol):
    # Создаем экземпляр объекта биржи
    exchange = ccxt.binance()

    # Устанавливаем нужные пары и временные интервалы

    # Функция для получения и вывода данных о цене и RSI
    try:
        # Получаем данные за последний интервал
        candles = exchange.fetch_ohlcv(symbol, '1h')

        # Получаем цену закрытия последней свечи
        last_close_price = candles[-1][4]

        # Получаем RSI
        rsi = calculate_rsi(candles)

        # Выводим результат
        print(f"RSI: {rsi}")

    except Exception as e:
        print(f"An error occurred: {e}")
