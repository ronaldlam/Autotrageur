"""Orderbook scraper.

Fetches orderbook data from a specified exchange.

Usage:
    ob_scraper.py EXCHANGE BASE QUOTE DBINFOFILE

Description:
    EXCHANGE            The exchange to scrape from.
    BASE                The base symbol.  E.g. 'eth'.
    QUOTE               The quote symbol.  E.g. 'usd'.
    DBINFOFILE          Database details, including database name and user.
"""
import getpass
import time
import uuid

import ccxt
import yaml
from docopt import docopt
from sqlalchemy import Column, ForeignKey, MetaData, Table, create_engine
from sqlalchemy.dialects.mysql import CHAR, DECIMAL, INTEGER, VARCHAR, insert
from sqlalchemy.sql import select

import libs.ccxt_extensions as ccxt_extensions
from libs.trade.fetcher.ccxt_fetcher import CCXTFetcher

EXTENSION_PREFIX = 'ext_'


if __name__ == "__main__":
    args = docopt(__doc__, version="ob_scraper 0.1")
    exchange = args['EXCHANGE'].lower()
    base = args['BASE'].upper()
    quote = args['QUOTE'].upper()
    db_info_file = args['DBINFOFILE']

    # Get DB details.
    with open(args['DBINFOFILE'], 'r') as db_info:
        db_info = yaml.safe_load(db_info)
        db_user = db_info['db_user']
        db_name = db_info['db_name']
    db_password = getpass.getpass(prompt="Enter database password:")

    # Setup DB engine, SQLAlchemy Metadata object, and connect.
    conn_string = ('mysql+mysqldb://'
                    + db_user
                    + ':'
                    + db_password
                    + '@localhost/'
                    + db_name)
    engine = create_engine(
        conn_string, pool_recycle=3600, pool_pre_ping=True, echo=True)
    alchemy_metadata = MetaData()
    conn = engine.connect()

    # Instantiate exchange object anf fetcher.
    if EXTENSION_PREFIX + exchange in dir(ccxt_extensions):
        ccxt_exchange = getattr(
            ccxt_extensions, EXTENSION_PREFIX + exchange)()
    else:
        ccxt_exchange = getattr(ccxt, exchange)()
    fetcher = CCXTFetcher(ccxt_exchange)

    # Load the markets and obtain orderbook.
    ccxt_exchange.load_markets()
    ccxt_ob_result = fetcher.get_full_orderbook(base, quote)

    # Create the ob_metadata table for the specified (exchange, base, quote) if
    # necessary.  If it exists, obtain the UUID and pass it to the orderbook
    # table.  If not, we create an entry and pass the UUID to the orderbook
    # table.
    ob_metadata = Table('ob_metadata', alchemy_metadata,
        Column('id', VARCHAR(length=36), nullable=False, primary_key=True),
        Column('base', VARCHAR(length=10), nullable=False),
        Column('quote', VARCHAR(length=10), nullable=False),
        Column('exchange', VARCHAR(length=28), nullable=False),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4')

    ob_metadata.create(engine, checkfirst=True)

    s = select([ob_metadata]).\
            where(ob_metadata.c.base == base).\
            where(ob_metadata.c.quote == quote).\
            where(ob_metadata.c.exchange == exchange)
    row = conn.execute(s).fetchone()

    # Doesn't exist, create an entry.
    if row is None:
        new_ob_table_stmt = insert(ob_metadata)
        table_id = str(uuid.uuid4())
        conn.execute(new_ob_table_stmt, id=table_id, base=base,
            quote=quote, exchange=exchange)
    else:
        table_id = row[ob_metadata.c.id]

    # Format the ccxt unified response to map into our database schema.
    ob_data = []

    # The ccxt response only has one timestamp entry, and it can be a single
    # timestamp or 'None' - even if the exchange returns distinct timestamps
    # per order.
    local_ts = int(time.time())
    order_ts = ccxt_ob_result['timestamp'] or local_ts
    for bid_order in ccxt_ob_result['bids']:
        ob_data.append(
            {
                'table_id': table_id,
                'local_unix_ts': local_ts,
                'exchange_ts': order_ts,
                'bid_ask': 'bid',
                'order_price': bid_order[0],
                'order_volume': bid_order[1]
            }
        )
    for ask_order in ccxt_ob_result['asks']:
        ob_data.append(
            {
                'table_id': table_id,
                'local_unix_ts': local_ts,
                'exchange_ts': order_ts,
                'bid_ask': 'ask',
                'order_price': ask_order[0],
                'order_volume': ask_order[1]
            }
        )
    print(ob_data)

    # Create table if needed and insert data.
    tablename = ''.join([exchange, base, quote])
    ob_table = Table(tablename, alchemy_metadata,
        Column('table_id', VARCHAR(length=36), ForeignKey('ob_metadata.id'),
            nullable=False),
        Column('local_unix_ts', INTEGER(display_width=11, unsigned=True),
            nullable=False),
        Column('exchange_ts', INTEGER(display_width=11, unsigned=True),
            nullable=False),
        Column('bid_ask', CHAR(length=3), nullable=False),
        Column('order_price', DECIMAL(precision=27, scale=8), nullable=False,
            primary_key=True),
        Column('order_volume', DECIMAL(precision=27, scale=8), nullable=False),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4')

    # `create_all` will check for if the table exists first, before attempting
    # creation.
    alchemy_metadata.create_all(engine)
    insert_stmt = insert(ob_table)
    on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
        order_price=insert_stmt.inserted.order_price)
    conn.execute(on_duplicate_key_stmt, ob_data)
