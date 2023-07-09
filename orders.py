import creds

def orderSell(sell_quantity, sell_price, order, client):
    order = client.order_limit_sell(
        symbol=creds.symbol,
        quantity=sell_quantity,
        price=sell_price
    )
    return order

def orderBuy(sell_quantity, sell_price, order, client):
    order = client.order_limit_buy(
        symbol=creds.symbol,
        quantity=sell_quantity,
        price=sell_price
    )
    
    return order

def checkOrder(client, orderId):
    order = client.get_order(symbol=creds.symbol, orderId=orderId)
    if order['status'] == 'FILLED':
        return True
    return False