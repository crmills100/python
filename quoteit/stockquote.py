import http.client
import json
import folio

##symbol = ['ADT', 'AM','CSCO','CWH']
##symbols = "%252C".join(symbol)

##DEBUG print(symbols)

##portfolio = {
##    'ADT': {'shares': [[274, 2]]},
##    'AM': {'shares': [[414, 2]]},
##    'CSCO': {'shares': [[59, 2]]},
##    'CWH': {'shares': [[100, 21.66], [252, 7.86]]}
##}

# TODO: add cmd line args to select filename
##filename = 'portfolio.csv'
filename = 'fidelity.csv'

portfolio = folio.buildPortfolio(filename)
symbol = portfolio.keys()
symbols = "%252C".join(symbol)

def readQuotesFromAPI(symbols):
        
    headers = {
        'x-rapidapi-host': "apidojo-yahoo-finance-v1.p.rapidapi.com",
        'x-rapidapi-key': "18e1664f8dmsh1e5771c544a38bcp173577jsn9a667c4db859"
    }
    
    conn = http.client.HTTPSConnection("apidojo-yahoo-finance-v1.p.rapidapi.com")
    
    conn.request("GET", "/market/v2/get-quotes?symbols=" + symbols + "&region=US", headers=headers)

    res = conn.getresponse()
    data = res.read()
    
    
    quotes = json.loads(data)

    f = open("data.txt", "w")
    f.write(json.dumps(quotes))
    f.close

    return quotes

def readQuotesFromFile(symbols):
    f = open("data.txt", "r")
    data = f.read()
    
    
    quotes = json.loads(data)

    return quotes
        
fromFile = False
quotes = {}

if (fromFile):
    quotes = readQuotesFromFile(symbols)
else:
    quotes = readQuotesFromAPI(symbols)

## f = open("data.txt", "w")
## f.write(json.dumps(quotes))
## f.close

q = quotes["quoteResponse"]["result"]

print("Symbol\tPrice\tPrevious\tChange\tBid\tAsk\tPre\tChange\tShares\tMarket\t\tCost")
print("      \t\tClose\t\t\t\t\t\tPre\t\tValue\t\tBasis/Share")

def buildMetrics(info, portfolio):
    sym = info["symbol"]
    change = info['regularMarketPrice'] - info['regularMarketPreviousClose']
    shares = 0.0
    costBasis = 0.0
    for s in portfolio[sym]['shares']:
        costBasis = costBasis + (s[0] * s[1])
        shares = shares + s[0]

    costPerShare = float("nan")
    if (shares != 0):
        costPerShare = costBasis / shares

    bid = info['bid']
    ask = info['ask']
    pre = 0
    changePre = 0
    if ('preMarketPrice' in info.keys()):
        pre = info['preMarketPrice']
        changePre = pre - info['regularMarketPrice']
    
    metrics = {
        'regularMarketPreviousClose': info['regularMarketPreviousClose'],
        'regularMarketPrice': info['regularMarketPrice'],
        'bid': info['bid'],
        'ask': info['ask'],
        'pre': pre,
        'symbol': sym,
        'change': change,
        'changePre': changePre,
        'shares': shares,
        'costBasis': costBasis,
        'costPerShare': costPerShare,
        'marketState': info['marketState'],
        'marketValue': (shares * info['regularMarketPrice'])
    }
    return metrics

marketState = ""
for info in q:

    metrics = buildMetrics(info, portfolio)

    close = metrics["regularMarketPreviousClose"]
    price = metrics["regularMarketPrice"]
    sym = info["symbol"]
    change = metrics["change"];

    if (marketState == ""):
        marketState = metrics['marketState']

    if (marketState != metrics['marketState']):
        print("ERROR: inconsistent market state")

    txt = "{sym} {marketState}:\t{price:> 6.2f}\t{close:> 6.2f}\t\t{change:> .2f}\t{bid:> 6.2f}\t{ask:> 6.2f}\t{pre:> 6.2f}\t{changePre:> .2f}\t{shares:> 5.0f}\t{marketValue:>8.2f}\t{costPerShare:>6.2f}\t{costBasis:>6.2f}".format(
        sym = sym,
        marketState = metrics['marketState'][0:1],
        price = price,
        close = close,
        change = change,
        bid = metrics['bid'],
        ask = metrics['ask'],
        pre = metrics['pre'],
        changePre = metrics['changePre'],
        shares = metrics['shares'],
        marketValue = metrics['marketValue'],
        costPerShare = metrics['costPerShare'],
        costBasis = metrics['costBasis']
    )
    print(txt)
    
quit()

print(info.decode("utf-8"))

