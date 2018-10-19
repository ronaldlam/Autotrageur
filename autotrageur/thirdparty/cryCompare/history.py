import requests


__histominuteurl = 'https://min-api.cryptocompare.com/data/histominute?'
__histohoururl = 'https://min-api.cryptocompare.com/data/histohour?'
__histodayurl = 'https://min-api.cryptocompare.com/data/histoday?'


def histoMinute(from_curr, to_curr, e=None, extraParams=None, sign=False, tryConversion=True, aggregate=None, limit=None, toTs=None):
	return __get_price(__histominuteurl, from_curr, to_curr, e, extraParams, sign, tryConversion, aggregate, limit, toTs)


def histoHour(from_curr, to_curr, e=None, extraParams=None, sign=False, tryConversion=True, aggregate=None, limit=None, toTs=None):
	return __get_price(__histohoururl, from_curr, to_curr, e, extraParams, sign, tryConversion, aggregate, limit, toTs)


def histoDay(from_curr, to_curr, e=None, extraParams=None, sign=False, tryConversion=True, aggregate=None, limit=None, toTs=None, allData=False):
	return __get_price(__histodayurl, from_curr, to_curr, e, extraParams, sign, tryConversion, aggregate, limit, toTs, allData)


def __get_price(baseurl, from_curr, to_curr, e=None, extraParams=None, sign=False,
				tryConversion=True, aggregate=None, limit=None, toTs=None, allData=False):
	args = list()
	if isinstance(from_curr, str):
		args.append('fsym=' + from_curr.upper())
	if isinstance(to_curr, str):
		args.append('tsym=' + to_curr.upper())
	if e:
		args.append('e=' + e)
	if extraParams:
		args.append('extraParams=' + extraParams)
	if sign:
		args.append('sign=true')
	if aggregate:
		args.append('aggregate=' + str(aggregate))
	if limit:
		args.append('limit=' + str(limit))
	if toTs:
		args.append('toTs=' + str(toTs))
	if allData:
		args.append('allData=true')
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
