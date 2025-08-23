import http.client
import json
import folio

conn = http.client.HTTPSConnection("apidojo-yahoo-finance-v1.p.rapidapi.com")
##symbol = ['ADT', 'AM','CSCO','CWH']
##symbols = "%252C".join(symbol)

##DEBUG print(symbols)

portfolio = {
    'ADT': {'shares': [[274, 2]]},
    'AM': {'shares': [[414, 2]]},
    'CSCO': {'shares': [[59, 2]]},
    'CWH': {'shares': [[100, 21.66], [252, 7.86]]}
}

# TODO: add cmd line args to select filename
filename = 'portfolio.csv'

portfolio = folio.buildPortfolio(filename)
symbol = portfolio.keys()
symbols = "%252C".join(symbol)

print(symbols)

headers = {
    'x-rapidapi-host': "apidojo-yahoo-finance-v1.p.rapidapi.com",
    'x-rapidapi-key': "18e1664f8dmsh1e5771c544a38bcp173577jsn9a667c4db859"
    }

conn.request("GET", "/market/v2/get-quotes?symbols=" + symbols + "&region=US", headers=headers)

res = conn.getresponse()
data = res.read()

quotes = json.loads(data)

## f = open("data.txt", "w")
## f.write(json.dumps(quotes))
## f.close

q = quotes["quoteResponse"]["result"]

print("Symbol\tLast\tPrevious\tChange\tShares\tMarket\t\tCost")
print("      \tClose\tClose\t\t\t\tValue\t\tBasis/Share")

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

    metrics = {
        'regularMarketPreviousClose': info['regularMarketPreviousClose'],
        'regularMarketPrice': info['regularMarketPrice'],
        'symbol': sym,
        'change': change,
        'shares': shares,
        'costBasis': costBasis,
        'costPerShare': costPerShare,
        'marketValue': (shares * info['regularMarketPrice'])
    }
    return metrics

for info in q:

    metrics = buildMetrics(info, portfolio)

    close = metrics["regularMarketPreviousClose"]
    price = metrics["regularMarketPrice"]
    sym = info["symbol"]
    change = metrics["change"];

    txt = "{sym}:\t{price:> 6.2f}\t{close:> 6.2f}\t\t{change:> .2f}\t{shares:> 4.0f}\t{marketValue:>8.2f}\t{costPerShare:>6.2f}\t{costBasis:>6.2f}".format(sym = sym, price = price, close = close, change = change, shares = metrics['shares'], marketValue = metrics['marketValue'], costPerShare = metrics['costPerShare'], costBasis = metrics['costBasis'])
    print(txt)
    
quit()

print(info.decode("utf-8"))

