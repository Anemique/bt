import requests
import pandas as pd
import ta

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