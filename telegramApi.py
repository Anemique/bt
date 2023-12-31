import requests
import creds      # Конфиг

def sendMessage(message):
  url = f"https://api.telegram.org/bot{creds.token}/sendMessage?chat_id={creds.chat_id}&text={message}"
  requests.get(url)

def messageResolver(type, args):
  if type == 'buy_placing':
    return ' \n' + '--------------------' + ' \n' + 'Выставлен ордер на покупку' + ' \n' + 'Цена: ' + str(args['sell_price']) + ' \n' + 'Количество: ' + str(args['sell_quantity']) + ' \n' + 'Потрачено: ' + str(args['buy_balance'])
  elif type == 'buy_filled':
    return ' \n' + 'Ордер на покупку выполнен'
  elif type == 'sell_placing':
    return ' \n' + 'Выставлен ордер на продажу' + ' \n' + 'Цена: ' + str(args['sell_price']) + ' \n' + 'Количество: ' + str(args['sell_quantity']) + ' \n'
  elif type == 'sell_filled':
    return ' \n' + 'Ордер на продажу выполнен' + ' \n' + 'Профит: ' + str(round(args['profit'] * 84, 2)) + ' руб' + ' \n' + 'Изменение: ' + str(args['balance_change']) + ' руб' + ' \n' + '--------------------'
  elif type == 'order_canceled':
    return ' \n' + 'Ордер на покупку отменен'
  elif type == 'sell_placing_stop':
    return ' \n' + 'Выставлен стоп-лосс' + ' \n' + 'Цена: ' + str(args['sell_price']) + ' \n' + 'Количество: ' + str(args['sell_quantity']) + ' \n'
  elif type == 'sell_filled_stop':
    return ' \n' + 'Стоп-лосс выполнен' + ' \n' + 'Профит: ' + str(round(args['profit'] * 84, 2)) + ' руб' + ' \n' + 'Изменение: ' + str(args['balance_change']) + ' руб' + ' \n' + '--------------------'

def telegramSend(type, args = {}):
  message = messageResolver(type, args)
  sendMessage(message)