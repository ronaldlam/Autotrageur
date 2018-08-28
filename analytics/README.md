# Analytics
Start at the top level directory of the project (Autotrageur).
### E.g. Running all 'minute' fetch scripts:
```source scripts/spawn_all_minute.sh``` and supply an encrypted db password file as an argument.  The script will prompt you to input the password and salt which you encrypted the file with.

This will spawn up to 5 fetchers to attain OHLC minute data from cryptocompare.

# Orderbook Scraper

## Exchange limits

| Exchange      | Max Limit | Default  |Reference                        |
| ------------- |:----------|:---------|:--------------------------------|
| Bithumb       | 50        | 20       |https://www.bithumb.com/u1/US127 |
| Gemini        | 2254      | 50       |https://docs.gemini.com/rest-api/#current-order-book|