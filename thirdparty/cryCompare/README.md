# cryCompare
Python wrapper for Crypto Compare public API

Following requests are supported:
- CoinList
- Price
- PriceMulti
- PriceMultiFull
- PriceHistorical
- CoinSnapshot
- CoinSnapshotFullById
- HistoMinute
- HistoHour
- HistoDay

Wrapper requires following python modules:
- requests

Usage

```
from crycompare import price as p
print(p.coinSnapshot('btc', 'usd'))
```

price module: price, priceMulti, priceMultiFull, generateAvg, dayAvg, priceHistorical, coinSnapshot, coinSnahpshotFullById.
For detailed documentation visit CryptoCompare API website.

history modyle: histoMinute, histoHour, histoDay.
For detailed documentation visit CryptoCompare API website.

CryptoCompare API Documentation can be found at https://www.cryptocompare.com/api/#introduction
