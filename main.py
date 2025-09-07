import time
import requests
import math
from decimal import Decimal, ROUND_DOWN
from binance.client import Client

# Klucze API (Upewnij się, że masz swoje API Key & Secret)
from config import API_KEY, API_SECRET


# Inicjalizacja klienta Binance Spot
client = Client(API_KEY, API_SECRET)

SYMBOL = "BTCPLN"  # Para handlowa
#SYMBOL = "BTCUSDC"
MIN_TRADE_AMOUNT = 25  # Minimalna kwota do handlu (25 PLN)
MAX_ILOSC_ZLECEN = 50

def round_to_tick(price, tick_size):
    d_price = Decimal(str(price))
    d_tick = Decimal(str(tick_size))
    return float((d_price // d_tick) * d_tick)

def log_message(message):
    """ Zapisuje wiadomości do pliku log.txt, dodając je na początku """

    # Pobierz aktualną datę i godzinę
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    # Odczytanie zawartości pliku, jeśli istnieje
    try:
        with open("logbtcpln.txt", "r") as log_file:
            content = log_file.read()
    except FileNotFoundError:
        # Jeśli plik nie istnieje, to po prostu stwórz pusty plik
        content = ""

    # Nowa zawartość, z datą i wiadomością na początku
    new_content = f"[{timestamp}] {message}\n" + content

    # Zapisanie nowej zawartości do pliku (nadpisuje plik)
    with open("logbtcpln.txt", "w") as log_file:
        log_file.write(new_content)

    # Wyświetlenie wiadomości w konsoli
    print(message)

def synchronize_binance_time():
    """ Synchronizuje czas z giełdą Binance """

    # Pobieranie czasu servera
    server_time = client.get_server_time()['serverTime']

    # Pobieranie czasu lokalnego
    local_time = int(time.time() * 1000)

    # Obliczanie różnicy czasu servera - lokalnego
    time_difference = server_time - local_time

    # Ustawienie różnicy czasu u klienta
    client.timestamp_offset = time_difference

def get_open_sell_orders():
    """ Pobiera ID zlecenia o najniższej i najwyższej cenie sprzedaży """

    # Pobieranie otwartych zleceń
    open_orders = client.get_open_orders(symbol=SYMBOL)

    # Filtrujemy tylko zlecenia sprzedaży SELL
    sell_orders = [order for order in open_orders if order["side"] == "SELL"]


    # Sprawdzenie czy są otwarte zlecenia sprzedaży
    if not sell_orders:
        print("Brak otwartych zleceń sprzedaży.")
        return None

    # Znajdujemy zlecenia o najniższej i najwyższej cenie
    min_price_order = min(sell_orders, key=lambda x: float(x["price"]))
    max_price_order = max(sell_orders, key=lambda x: float(x["price"]))

    #print(f"🟢 Najtańsze zlecenie: OrderID {min_price_order['orderId']}, Cena: {min_price_order['pr ice']}" )
    #print(f"🔴Najdroższe zlecenie: OrderID {max_price_order['orderId']}, Cena: {max_price_order['price']}")

    return float(min_price_order['price']), float(max_price_order['price'])

def buy_btc_for_pln(amount_pln, SYMBOL):
    SYMBOL = SYMBOL.upper()  # upewnij się, że jest BTCPLN

    # 1. Pobierz cenę BTC/PLN
    price = float(client.get_symbol_ticker(symbol=SYMBOL)["price"])
    print(f"Aktualna cena BTC: {price} PLN")

    # 2. Pobierz informacje o symbolu
    exchange_info = client.get_symbol_info(SYMBOL)

    # 3. Pobierz step_size, tick_size i minNotional
    step_size = 0.0
    tick_size = 0.0
    min_notional = 0.0
    for f in exchange_info["filters"]:
        if f["filterType"] == "LOT_SIZE":
            step_size = float(f["stepSize"])
        if f["filterType"] == "PRICE_FILTER":
            tick_size = float(f["tickSize"])
        if f["filterType"] == "MIN_NOTIONAL":
            min_notional = float(f["minNotional"])

    # 4. Sprawdź minimalną wartość zlecenia
    if amount_pln < min_notional:
        print(f"❌ Kwota {amount_pln} PLN jest zbyt niska. Minimalna wartość to {min_notional} PLN.")
        return None

    # 5. Oblicz ilość BTC za podaną kwotę PLN
    btc_amount = amount_pln / price

    # 6. Zaokrągl ilość BTC do step_size
    btc_amount = math.floor(btc_amount / step_size) * step_size
    btc_amount_str = "{:.8f}".format(btc_amount).rstrip('0').rstrip('.')

    print(f"✅ Kupuję {btc_amount_str} BTC za {amount_pln} PLN")

    # 7. Market BUY
    order = client.order_market_buy(symbol=SYMBOL, quantity=btc_amount_str)
    print("✅ Zlecenie BUY złożone:", order)

    time.sleep(1)

    # Oblicz średnią cenę zakupu
    avg_price = float(order['cummulativeQuoteQty']) / float(order['executedQty'])

    # Oblicz cenę sprzedaży z narzutem 1%
    raw_sell_price = avg_price * 1.01
    sell_price = round_to_tick(raw_sell_price, tick_size)


    # Ilość do sprzedaży (opcjonalnie możesz zmniejszyć nieco, aby uniknąć błędów typu "lot size")
    sell_quantity = float(order['executedQty']) * 0.999  # np. zostawiamy 0.1% na prowizję
    sell_quantity = round(sell_quantity, 6)  # zależy od symbolu – np. BTCUSDT ma precision 6

    print(f"📈 Wystawiam SELL LIMIT: {sell_quantity} BTC po {sell_price} PLN (+1%)")


    # 9. Limit SELL
    sell_order = client.order_limit_sell(
        symbol=SYMBOL,
        quantity=sell_quantity,
        price=sell_price
    )
    print("✅ Zlecenie SELL złożone:", sell_order)

    return order, sell_order

def floor_5(value):
    return math.floor(value * 10**5) / 10**5

def get_balance():
    """ Pobiera dostępne saldo danego assetu """
    balances = client.get_account()["balances"]
    price = float(client.get_symbol_ticker(symbol=SYMBOL)["price"])

    for balance in balances:
        if balance["asset"] == "BTC":
            #print(type(balance["free"]))
            balancebtc = float(balance["free"])+float(balance["locked"])
            #balance = str(balance)
            balancebtc = balancebtc*price
        if balance["asset"] == "PLN":
            balancepln = float(balance["free"])+float(balance["locked"])

    wielkosc_zlecenia = floor_5((balancebtc+balancepln)/MAX_ILOSC_ZLECEN)

    return balancebtc,balancepln,balancebtc+balancepln,wielkosc_zlecenia

def get_ath():
    klines = client.get_historical_klines(SYMBOL, Client.KLINE_INTERVAL_1WEEK, "8 year ago UTC")
    prices = [float(c[2]) for c in klines]  # high
    return max(prices)



while True:

    try:
        print("Working...")
        synchronize_binance_time()



        if get_balance()[1] >= get_balance()[3]:
            if get_open_sell_orders() == None:
                buy_btc_for_pln(get_balance()[3], SYMBOL)
                print("Buy")
            else:
                min_order = get_open_sell_orders()[0]
                price = float(client.get_symbol_ticker(symbol=SYMBOL)["price"])

                if price <= min_order - ((min_order*0.005 + (get_ath()*0.01))):
                    print("Buy")
                    buy_btc_for_pln(get_balance()[3], SYMBOL)

    except Exception as e:

        log_message(f"X Inny błąd: {e}")

        pass

    time.sleep(5)