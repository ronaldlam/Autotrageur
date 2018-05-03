import requests


__coinlisturl = 'https://www.cryptocompare.com/api/data/coinlist/'
__priceurl = 'https://min-api.cryptocompare.com/data/price?'
__pricemultiurl = 'https://min-api.cryptocompare.com/data/pricemulti?'
__pricemultifullurl = 'https://min-api.cryptocompare.com/data/pricemultifull?'
__generateavgurl = 'https://min-api.cryptocompare.com/data/generateAvg?'
__dayavgurl = 'https://min-api.cryptocompare.com/data/dayAvg?'
__historicalurl = 'https://min-api.cryptocompare.com/data/pricehistorical?'
__coinsnapshoturl = 'https://www.cryptocompare.com/api/data/coinsnapshot/?'
__coinsnapshotfull = 'https://www.cryptocompare.com/api/data/coinsnapshotfullbyid/?'


def coinList():
	return __get_url(__coinlisturl)


def price(from_curr, to_curr, e=None, extraParams=None, sign=False, tryConversion=True):
	return __get_price(__priceurl, from_curr, to_curr, e, extraParams, sign, tryConversion)


def priceMulti(from_curr, to_curr, e=None, extraParams=None, sign=False, tryConversion=True):
	return __get_price(__pricemultiurl, from_curr, to_curr, e, extraParams, sign, tryConversion)


def priceMultiFull(from_curr, to_curr, e=None, extraParams=None, sign=False, tryConversion=True):
	return __get_price(self.__pricemultifullurl, from_curr, to_curr, e, extraParams, sign, tryConversion)


def priceHistorical(from_curr, to_curr, markets, ts=None, e=None, extraParams=None,
					sign=False, tryConversion=True):
	return __get_price(__historicalurl, from_curr, to_curr, markets, ts, e, extraParams, sign, tryConversion)


def generateAvg(from_curr, to_curr, markets, extraParams=None, sign=False, tryConversion=True):
	return __get_avg(__generateavgurl, from_curr, to_curr, markets, extraParams, sign, tryConversion)


def dayAvg(self, from_curr, to_curr, e=None, extraParams=None, sign=False, tryConversion=True,
		   avgType=None, UTCHourDiff=0, toTs=None):
	return __get_avg(self.__dayavgurl, from_curr, to_curr, e, extraParams, sign,
						tryConversion, avgType, UTCHourDiff, toTs)


def coinSnapshot(from_curr, to_curr):
	return __get_url(__coinsnapshoturl + 'fsym=' + from_curr.upper() + '&tsym=' + to_curr.upper())


def coinSnapshotFullById(coin_id):
	return __get_url(__coinsnapshotfull + 'id=' + str(coin_id))


def __get_price(baseurl, from_curr, to_curr, e=None, extraParams=None, sign=False,
			  tryConversion=True, markets=None, ts=None):
	args = list()
	if isinstance(from_curr, str):
		args.append('fsym=' + from_curr.upper())
	elif isinstance(from_curr, list):
		args.append('fsyms=' + ','.join(from_curr).upper())
	if isinstance(to_curr, list):
		args.append('tsyms=' + ','.join(to_curr).upper())
	elif isinstance(to_curr, str):
		args.append('tsyms=' + to_curr.upper())
	if isinstance(markets, str):
		args.append('markets=' + markets)
	elif isinstance(markets, list):
		args.append('markets=' + ','.join(markets))
	if e:
		args.append('e=' + e)
	if extraParams:
		args.append('extraParams=' + extraParams)
	if sign:
		args.append('sign=true')
	if ts:
		args.append('ts=' + str(ts))
	if not tryConversion:
		args.append('tryConversion=false')
	if len(args) >= 2:
		return __get_url(baseurl + '&'.join(args))
	else:
		raise ValueError('Must have both fsym and tsym arguments.')


def __get_avg(baseurl, from_curr, to_curr, markets=None, e=None, extraParams=None,
			sign=False, tryConversion=True, avgType=None, UTCHourDiff=0, toTs=None):
	args = list()
	if isinstance(from_curr, str):
		args.append('fsym=' + from_curr.upper())
	if isinstance(to_curr, str):
		args.append('tsym=' + to_curr.upper())
	if isinstance(markets, str):
		args.append('markets=' + markets)
	elif isinstance(markets, list):
		args.append('markets=' + ','.join(markets))
	if e:
		args.append('e=' + e)
	if extraParams:
		args.append('extraParams=' + extraParams)
	if sign:
		args.append('sign=true')
	if avgType:
		args.append('avgType=' + avgType)
	if UTCHourDiff:
		args.append('UTCHourDiff=' + str(UTCHourDiff))
	if toTs:
		args.append('toTs=' + toTs)
	if not tryConversion:
		args.append('tryConversion=false')
	if len(args) >= 2:
		return __get_url(baseurl + '&'.join(args))
	else:
		raise ValueError('Must have both fsym and tsym arguments.')


def __get_url(url):
	raw_data = requests.get(url)
	raw_data.encoding = 'utf-8'
	if raw_data.status_code != 200:
		raw_data.raise_for_status()
		return False
	try:
		return raw_data.json()['Data']
	except NameError:
		raise ValueError('Cannot parse to json.')
