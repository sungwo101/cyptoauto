import time
import pyupbit
import datetime
import numpy as np
import pandas

access = ""          # 본인 값으로 변경
secret = ""          # 본인 값으로 변경

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, "minute240", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def get_ror(k=0.5):
    df = pyupbit.get_ohlcv("KRW-ETH", count=7)
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)

    df['ror'] = np.where(df['high'] > df['target'],
                        df['close'] / df['target'],
                        1)

    ror = df['ror'].cumprod()[-2]
    return ror

def rsi(ohlc: pandas.DataFrame, period: int = 14):
    delta = ohlc["close"].diff()
    ups, downs = delta.copy(), delta.copy()
    ups[ups < 0] = 0
    downs[downs > 0] = 0

    AU = ups.ewm(com = period-1, min_periods = period).mean()
    AD = downs.abs().ewm(com = period-1, min_periods = period).mean()
    RS = AU/AD

    return pandas.Series(100 - (100/(1 + RS)), name = "RSI")  

def ATR(coin):
    global High, Low

    c_2 = pyupbit.get_ohlcv(coin, count=2)
    pre = c_2.iloc[0]
    p_close = pre['close']

    minute240 = pyupbit.get_ohlcv(coin, "minute240", count=1)
    High = minute240['high'].max()
    Low = minute240['low'].max()

    # ATR
    ATR_1 = High - Low
    ATR_2 = abs(High - p_close)
    ATR_3 = abs(p_close - Low)
    ATR_L = [ATR_1, ATR_2, ATR_3]
    ATR = max(ATR_L)

    return ATR


def buy(coin, price):
    upbit.buy_market_order(coin, price*0.9995)
    return

def sell(coin, price):
    upbit.sell_market_order(coin, price*0.9995)
    return


# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

k = 0.2
i = 1
item = "KRW-ETH"
lower28 = 0
higher70 = 0
b_price = 0


# 자동매매 시작
while 1:
    global High, Low
    try:

        now = datetime.datetime.now()
        start_time = get_start_time(item)
        end_time = start_time + datetime.timedelta(days=1)

        if start_time < now < end_time - datetime.timedelta(seconds=10):
            data = pyupbit.get_ohlcv(ticker=item, interval="minute240")  
            now_rsi = rsi(data, 14).iloc[-1]
            target_price = get_target_price(item, k)
            current_price = get_current_price(item)

            if now_rsi <= 28 : 
                lower28 = 1

            elif now_rsi >= 33 and lower28 == 1 and target_price < current_price:
                krw = get_balance("KRW")

                if krw > 1000:
                    buy(item, krw)
                    lower28 = 0
                    b_price = current_price
                    print("We bought!!\n")
                    
            elif current_price <= b_price - ATR(item)*2:
                """손절라인 정하기"""
                sell(item, btc)
                b_price = 0
                print("Fuck.... we sold\n")

            elif now_rsi >= 70 and higher70 == 0 :
                '''익절'''
                btc = get_balance("ETH")
                if btc > 0.002:
                    sell(item, btc)
                    higher70 = 1
                    b_price = 0
                    print("Fuck yes!!! I got the money\n")

            elif current_price >= High - ATR(item)*2:
                btc = get_balance("ETH")
                if btc > 0.002:
                    sell(item, btc)
                    b_price = 0
                    print("Fuck yes!!! I got the money\n")



            elif now_rsi <= 60:
                higher70 = 0
            print("RSI : %f\n" %now_rsi)

        else:
            r={}

            for kk in np.arange(0.1, 1.0, 0.1):
                ror = get_ror(kk)
                r[ror]=kk
                #print("%.1f %f" % (kk, ror))

            rv = list(r.keys())
            m_rv = max(rv)
            k = r.get(m_rv)
            print("k(%d) : %.1f" %(i, k))
            i += 1
                
        time.sleep(1)

    except Exception as e:
        print(e)
        time.sleep(1)
