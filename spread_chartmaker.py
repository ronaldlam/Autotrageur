"""Creates charts to analyze spreads between two sets of data.

Usage:
    spread_chartmaker.py DATASET1 DATASET2

Options:
-h --help       Requires two dataset inputs.  Could be two paths/to/csvfiles.
"""
from docopt import docopt
import pandas as pd

import plotly
import plotly.graph_objs as go

from datetime import datetime as dt


if __name__ == "__main__":
    args = docopt(__doc__, version='spread_chartmaker 1.0')
    ds1_df = pd.read_csv(args['DATASET1'])
    ds2_df = pd.read_csv(args['DATASET2'])

    raw_spread = ds2_df['vwap'] / ds1_df['vwap']
    raw_spread = ((raw_spread - 1)*100)

    # converts unix timestamp to datetime
    ds2_df.time = pd.to_datetime(ds2_df.time, unit='s')
    ds1_df.time = pd.to_datetime(ds1_df.time, unit='s')

    data = [
        go.Scatter(x=ds1_df.time, y=ds1_df.vwap, mode='lines+markers', text=raw_spread, name="bitfinex"),
        go.Scatter(x=ds2_df.time, y=ds2_df.vwap, mode='lines+markers', name="gdax")
    ]
    plotly.offline.plot(data, filename="test_graph")
