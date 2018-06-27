from decimal import Decimal


BUY_RESPONSES = [
    {
        'create_order': {
            "info": {
                "order_id": "97580675",
                "id": "97580675",
                "symbol": "ethusd",
                "exchange": "gemini",
                "avg_execution_price": "398.00",
                "side": "buy",
                "type": "exchange limit",
                "timestamp": "1529617177",
                "timestampms": 1529617177985,
                "is_live": False,
                "is_cancelled": False,
                "is_hidden": False,
                "was_forced": False,
                "executed_amount": "0.1",
                "remaining_amount": "0",
                "client_order_id": "1529617171779",
                "options": [
                    "immediate-or-cancel"
                ],
                "price": "412.00",
                "original_amount": "0.1"
            },
            "id": "97580675"
        },
        'fetch_my_trades': [
            {
                "id": "97580677",
                "order": "97580675",
                "info": {
                    "price": "398.00",
                    "amount": "0.1",
                    "timestamp": 1529617177,
                    "timestampms": 1529617177985,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0995",
                    "tid": 97580677,
                    "order_id": "97580675",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1529617171779"
                },
                "timestamp": 1529617177985,
                "datetime": "2018-06-21T21: 39: 38.985Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 39.800000000000004,
                "amount": 0.1,
                "fee": {
                    "cost": 0.0995,
                    "currency": "USD"
                }
            }
        ]
    },
    {
        'create_order': {
            "info": {
                "order_id": "99210252",
                "id": "99210252",
                "symbol": "ethusd",
                "exchange": "gemini",
                "avg_execution_price": "179.3333333333333333333333333333333",
                "side": "buy",
                "type": "exchange limit",
                "timestamp": "1530092517",
                "timestampms": 1530092517716,
                "is_live": False,
                "is_cancelled": False,
                "is_hidden": False,
                "was_forced": False,
                "executed_amount": "0.3",
                "remaining_amount": "0",
                "client_order_id": "1530092518169",
                "options": [
                    "immediate-or-cancel"
                ],
                "price": "200.00",
                "original_amount": "0.3"
            },
            "id": "99210252"
        },
        'fetch_my_trades': [
            {
                "id": "93023095",
                "order": "93023093",
                "info": {
                    "price": "37.48",
                    "amount": "1",
                    "timestamp": 1522374592,
                    "timestampms": 1522374592522,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0937",
                    "tid": 93023095,
                    "order_id": "93023093",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1522374592"
                },
                "timestamp": 1522374592522,
                "datetime": "2018-03-30T01: 49: 53.522Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 37.48,
                "cost": 37.48,
                "amount": 1.0,
                "fee": {
                    "cost": 0.0937,
                    "currency": "USD"
                }
            },
            {
                "id": "93023113",
                "order": "93023111",
                "info": {
                    "price": "37.48",
                    "amount": "1",
                    "timestamp": 1522374785,
                    "timestampms": 1522374785789,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0937",
                    "tid": 93023113,
                    "order_id": "93023111",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1522374786"
                },
                "timestamp": 1522374785789,
                "datetime": "2018-03-30T01: 53: 06.789Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 37.48,
                "cost": 37.48,
                "amount": 1.0,
                "fee": {
                    "cost": 0.0937,
                    "currency": "USD"
                }
            },
            {
                "id": "93024394",
                "order": "93024392",
                "info": {
                    "price": "37.48",
                    "amount": "0.5",
                    "timestamp": 1522395847,
                    "timestampms": 1522395847069,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.04685",
                    "tid": 93024394,
                    "order_id": "93024392",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1522395847"
                },
                "timestamp": 1522395847069,
                "datetime": "2018-03-30T07: 44: 07.690Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 37.48,
                "cost": 18.74,
                "amount": 0.5,
                "fee": {
                    "cost": 0.04685,
                    "currency": "USD"
                }
            },
            {
                "id": "93565883",
                "order": "93565881",
                "info": {
                    "price": "222.00",
                    "amount": "0.022523",
                    "timestamp": 1523781354,
                    "timestampms": 1523781354442,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500265",
                    "tid": 93565883,
                    "order_id": "93565881",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1523781355"
                },
                "timestamp": 1523781354442,
                "datetime": "2018-04-15T08: 35: 54.442Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 222.0,
                "cost": 5.000106000000001,
                "amount": 0.022523,
                "fee": {
                    "cost": 0.012500265,
                    "currency": "USD"
                }
            },
            {
                "id": "93817225",
                "order": "93817223",
                "info": {
                    "price": "450.00",
                    "amount": "0.011111",
                    "timestamp": 1523993651,
                    "timestampms": 1523993651053,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012499875",
                    "tid": 93817225,
                    "order_id": "93817223",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1523993653"
                },
                "timestamp": 1523993651053,
                "datetime": "2018-04-17T19: 34: 11.530Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 450.0,
                "cost": 4.99995,
                "amount": 0.011111,
                "fee": {
                    "cost": 0.012499875,
                    "currency": "USD"
                }
            },
            {
                "id": "93860188",
                "order": "93860186",
                "info": {
                    "price": "450.00",
                    "amount": "0.011111",
                    "timestamp": 1523994779,
                    "timestampms": 1523994779522,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012499875",
                    "tid": 93860188,
                    "order_id": "93860186",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1523994781"
                },
                "timestamp": 1523994779522,
                "datetime": "2018-04-17T19: 53: 00.522Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 450.0,
                "cost": 4.99995,
                "amount": 0.011111,
                "fee": {
                    "cost": 0.012499875,
                    "currency": "USD"
                }
            },
            {
                "id": "93891062",
                "order": "93891060",
                "info": {
                    "price": "450.00",
                    "amount": "0.011111",
                    "timestamp": 1524008814,
                    "timestampms": 1524008814271,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012499875",
                    "tid": 93891062,
                    "order_id": "93891060",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524008816"
                },
                "timestamp": 1524008814271,
                "datetime": "2018-04-17T23: 46: 54.271Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 450.0,
                "cost": 4.99995,
                "amount": 0.011111,
                "fee": {
                    "cost": 0.012499875,
                    "currency": "USD"
                }
            },
            {
                "id": "93891299",
                "order": "93891297",
                "info": {
                    "price": "450.00",
                    "amount": "0.011111",
                    "timestamp": 1524015070,
                    "timestampms": 1524015070735,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012499875",
                    "tid": 93891299,
                    "order_id": "93891297",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524015070"
                },
                "timestamp": 1524015070735,
                "datetime": "2018-04-18T01: 31: 11.735Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 450.0,
                "cost": 4.99995,
                "amount": 0.011111,
                "fee": {
                    "cost": 0.012499875,
                    "currency": "USD"
                }
            },
            {
                "id": "93891312",
                "order": "93891310",
                "info": {
                    "price": "450.00",
                    "amount": "0.011111",
                    "timestamp": 1524015342,
                    "timestampms": 1524015342226,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012499875",
                    "tid": 93891312,
                    "order_id": "93891310",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524015342"
                },
                "timestamp": 1524015342226,
                "datetime": "2018-04-18T01: 35: 42.226Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 450.0,
                "cost": 4.99995,
                "amount": 0.011111,
                "fee": {
                    "cost": 0.012499875,
                    "currency": "USD"
                }
            },
            {
                "id": "94272781",
                "order": "94272779",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524197468,
                    "timestampms": 1524197468933,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94272781,
                    "order_id": "94272779",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524197468"
                },
                "timestamp": 1524197468933,
                "datetime": "2018-04-20T04: 11: 09.933Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94272810",
                "order": "94272808",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524197713,
                    "timestampms": 1524197713327,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94272810,
                    "order_id": "94272808",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524197713"
                },
                "timestamp": 1524197713327,
                "datetime": "2018-04-20T04: 15: 13.327Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94272881",
                "order": "94272879",
                "info": {
                    "price": "99.48",
                    "amount": "0.050261",
                    "timestamp": 1524198343,
                    "timestampms": 1524198343466,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0124999107",
                    "tid": 94272881,
                    "order_id": "94272879",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524198343"
                },
                "timestamp": 1524198343466,
                "datetime": "2018-04-20T04: 25: 43.466Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 99.48,
                "cost": 4.99996428,
                "amount": 0.050261,
                "fee": {
                    "cost": 0.0124999107,
                    "currency": "USD"
                }
            },
            {
                "id": "94272927",
                "order": "94272925",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524198446,
                    "timestampms": 1524198446293,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94272927,
                    "order_id": "94272925",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524198446"
                },
                "timestamp": 1524198446293,
                "datetime": "2018-04-20T04: 27: 26.293Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94272958",
                "order": "94272956",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524198857,
                    "timestampms": 1524198857521,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94272958,
                    "order_id": "94272956",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524198857"
                },
                "timestamp": 1524198857521,
                "datetime": "2018-04-20T04: 34: 18.521Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94273367",
                "order": "94273365",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524204632,
                    "timestampms": 1524204632400,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94273367,
                    "order_id": "94273365",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524204632"
                },
                "timestamp": 1524204632400,
                "datetime": "2018-04-20T06: 10: 32.400Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94273386",
                "order": "94273384",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524205024,
                    "timestampms": 1524205024905,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94273386,
                    "order_id": "94273384",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524205024"
                },
                "timestamp": 1524205024905,
                "datetime": "2018-04-20T06: 17: 05.905Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94273397",
                "order": "94273395",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524205218,
                    "timestampms": 1524205218956,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94273397,
                    "order_id": "94273395",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524205218"
                },
                "timestamp": 1524205218956,
                "datetime": "2018-04-20T06: 20: 19.956Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94343771",
                "order": "94343769",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524432181,
                    "timestampms": 1524432181599,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94343771,
                    "order_id": "94343769",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524432179"
                },
                "timestamp": 1524432181599,
                "datetime": "2018-04-22T21: 23: 02.599Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94343776",
                "order": "94343774",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524432211,
                    "timestampms": 1524432211593,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94343776,
                    "order_id": "94343774",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524432211"
                },
                "timestamp": 1524432211593,
                "datetime": "2018-04-22T21: 23: 32.593Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94437307",
                "order": "94437305",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524524300,
                    "timestampms": 1524524300380,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94437307,
                    "order_id": "94437305",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524524300085"
                },
                "timestamp": 1524524300380,
                "datetime": "2018-04-23T22: 58: 20.380Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94445024",
                "order": "94445022",
                "info": {
                    "price": "397.00",
                    "amount": "0.012594",
                    "timestamp": 1524633587,
                    "timestampms": 1524633587235,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012499545",
                    "tid": 94445024,
                    "order_id": "94445022",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524633587162"
                },
                "timestamp": 1524633587235,
                "datetime": "2018-04-25T05: 19: 47.235Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 397.0,
                "cost": 4.999817999999999,
                "amount": 0.012594,
                "fee": {
                    "cost": 0.012499545,
                    "currency": "USD"
                }
            },
            {
                "id": "94445366",
                "order": "94445364",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524638635,
                    "timestampms": 1524638635333,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94445366,
                    "order_id": "94445364",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524638635042"
                },
                "timestamp": 1524638635333,
                "datetime": "2018-04-25T06: 43: 55.333Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94445597",
                "order": "94445595",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524644893,
                    "timestampms": 1524644893657,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94445597,
                    "order_id": "94445595",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524644893331"
                },
                "timestamp": 1524644893657,
                "datetime": "2018-04-25T08: 28: 14.657Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94445602",
                "order": "94445600",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524644907,
                    "timestampms": 1524644907794,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94445602,
                    "order_id": "94445600",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524644907468"
                },
                "timestamp": 1524644907794,
                "datetime": "2018-04-25T08: 28: 28.794Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94527341",
                "order": "94527339",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1525242567,
                    "timestampms": 1525242567776,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94527341,
                    "order_id": "94527339",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1525242567687"
                },
                "timestamp": 1525242567776,
                "datetime": "2018-05-02T06: 29: 28.776Z",
                "symbol": "ETH/USD",
                "type":
                None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94616276",
                "order": "94616274",
                "info": {
                    "price": "398.00",
                    "amount": "0.012562",
                    "timestamp": 1526183096,
                    "timestampms": 1526183096513,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.01249919",
                    "tid": 94616276,
                    "order_id": "94616274",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1526183096427"
                },
                "timestamp": 1526183096513,
                "datetime": "2018-05-13T03: 44: 57.513Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 4.999676,
                "amount": 0.012562,
                "fee": {
                    "cost": 0.01249919,
                    "currency": "USD"
                }
            },
            {
                "id": "97546905",
                "order": "97546903",
                "info": {
                    "price": "394.10",
                    "amount": "0.001",
                    "timestamp": 1529616497,
                    "timestampms": 1529616497632,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.00098525",
                    "tid": 97546905,
                    "order_id": "97546903",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1529616491439"
                },
                "timestamp": 1529616497632,
                "datetime": "2018-06-21T21: 28: 18.632Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 394.1,
                "cost": 0.3941,
                "amount": 0.001,
                "fee": {
                    "cost": 0.00098525,
                    "currency": "USD"
                }
            },
            {
                "id": "97580677",
                "order": "97580675",
                "info": {
                    "price": "398.00",
                    "amount": "0.1",
                    "timestamp": 1529617177,
                    "timestampms": 1529617177985,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0995",
                    "tid": 97580677,
                    "order_id": "97580675",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1529617171779"
                },
                "timestamp": 1529617177985,
                "datetime": "2018-06-21T21: 39: 38.985Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 39.800000000000004,
                "amount": 0.1,
                "fee": {
                    "cost": 0.0995,
                    "currency": "USD"
                }
            },
            {
                "id": "97866234",
                "order": "97866232",
                "info": {
                    "price": "394.10",
                    "amount": "0.001",
                    "timestamp": 1529623001,
                    "timestampms": 1529623001878,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.00098525",
                    "tid": 97866234,
                    "order_id": "97866232",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1529623001793"
                },
                "timestamp": 1529623001878,
                "datetime": "2018-06-21T23: 16: 42.878Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 394.1,
                "cost": 0.3941,
                "amount": 0.001,
                "fee": {
                    "cost": 0.00098525,
                    "currency": "USD"
                }
            },
            {
                "id": "97869134",
                "order": "97869132",
                "info": {
                    "price": "394.10",
                    "amount": "0.001",
                    "timestamp": 1529623046,
                    "timestampms": 1529623046764,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.00098525",
                    "tid": 97869134,
                    "order_id": "97869132",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1529623043770"
                },
                "timestamp": 1529623046764,
                "datetime": "2018-06-21T23: 17: 27.764Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 394.1,
                "cost": 0.3941,
                "amount": 0.001,
                "fee": {
                    "cost": 0.00098525,
                    "currency": "USD"
                }
            },
            {
                "id": "98645283",
                "order": "98645281",
                "info": {
                    "price": "398.00",
                    "amount": "0.1",
                    "timestamp": 1529647877,
                    "timestampms": 1529647877854,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0995",
                    "tid": 98645283,
                    "order_id": "98645281",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1529647877508"
                },
                "timestamp": 1529647877854,
                "datetime": "2018-06-22T06: 11: 18.854Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 39.800000000000004,
                "amount": 0.1,
                "fee": {
                    "cost": 0.0995,
                    "currency": "USD"
                }
            },
            {
                "id": "98645699",
                "order": "98645697",
                "info": {
                    "price": "398.00",
                    "amount": "0.1",
                    "timestamp": 1529647902,
                    "timestampms": 1529647902534,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0995",
                    "tid": 98645699,
                    "order_id": "98645697",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1529647902187"
                },
                "timestamp": 1529647902534,
                "datetime": "2018-06-22T06: 11: 43.534Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 39.800000000000004,
                "amount": 0.1,
                "fee": {
                    "cost": 0.0995,
                    "currency": "USD"
                }
            },
            {
                "id": "98654969",
                "order": "98654967",
                "info": {
                    "price": "398.00",
                    "amount": "0.1",
                    "timestamp": 1529648466,
                    "timestampms": 1529648466481,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0995",
                    "tid": 98654969,
                    "order_id": "98654967",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1529648466127"
                },
                "timestamp": 1529648466481,
                "datetime": "2018-06-22T06: 21: 06.481Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 39.800000000000004,
                "amount": 0.1,
                "fee": {
                    "cost": 0.0995,
                    "currency": "USD"
                }
            },
            {
                "id": "98655124",
                "order": "98655120",
                "info": {
                    "price": "398.00",
                    "amount": "0.1",
                    "timestamp": 1529648478,
                    "timestampms": 1529648478948,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0995",
                    "tid": 98655124,
                    "order_id": "98655120",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1529648478595"
                },
                "timestamp": 1529648478948,
                "datetime": "2018-06-22T06: 21: 19.948Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 39.800000000000004,
                "amount": 0.1,
                "fee": {
                    "cost": 0.0995,
                    "currency": "USD"
                }
            },
            {
                "id": "98659625",
                "order": "98659623",
                "info": {
                    "price": "398.00",
                    "amount": "0.1",
                    "timestamp": 1529648756,
                    "timestampms": 1529648756216,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0995",
                    "tid": 98659625,
                    "order_id": "98659623",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1529648755867"
                },
                "timestamp": 1529648756216,
                "datetime": "2018-06-22T06: 25: 56.216Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 39.800000000000004,
                "amount": 0.1,
                "fee": {
                    "cost": 0.0995,
                    "currency": "USD"
                }
            },
            {
                "id": "99208728",
                "order": "99208726",
                "info": {
                    "price": "181.91",
                    "amount": "0.01",
                    "timestamp": 1530055656,
                    "timestampms": 1530055656687,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.00454775",
                    "tid": 99208728,
                    "order_id": "99208726",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530055658856"
                },
                "timestamp": 1530055656687,
                "datetime": "2018-06-26T23: 27: 37.687Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 181.91,
                "cost": 1.8191,
                "amount": 0.01,
                "fee": {
                    "cost": 0.00454775,
                    "currency": "USD"
                }
            },
            {
                "id": "99208984",
                "order": "99208982",
                "info": {
                    "price": "181.91",
                    "amount": "0.01",
                    "timestamp": 1530061088,
                    "timestampms": 1530061088112,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.00454775",
                    "tid": 99208984,
                    "order_id": "99208982",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530061090427"
                },
                "timestamp": 1530061088112,
                "datetime": "2018-06-27T00: 58: 08.112Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 181.91,
                "cost": 1.8191,
                "amount": 0.01,
                "fee": {
                    "cost": 0.00454775,
                    "currency": "USD"
                }
            },
            {
                "id": "99209017",
                "order": "99209015",
                "info": {
                    "price": "181.91",
                    "amount": "0.01",
                    "timestamp": 1530061928,
                    "timestampms": 1530061928236,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.00454775",
                    "tid": 99209017,
                    "order_id": "99209015",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530061930526"
                },
                "timestamp": 1530061928236,
                "datetime": "2018-06-27T01: 12: 08.236Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 181.91,
                "cost": 1.8191,
                "amount": 0.01,
                "fee": {
                    "cost": 0.00454775,
                    "currency": "USD"
                }
            },
            {
                "id": "99209067",
                "order": "99209059",
                "info": {
                    "price": "7.80",
                    "amount": "0.002307",
                    "timestamp": 1530062782,
                    "timestampms": 1530062782395,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0000449865",
                    "tid": 99209067,
                    "order_id": "99209059",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530062784769"
                },
                "timestamp": 1530062782395,
                "datetime": "2018-06-27T01: 26: 22.395Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 7.8,
                "cost": 0.0179946,
                "amount": 0.002307,
                "fee": {
                    "cost": 4.49865e-05,
                    "currency": "USD"
                }
            },
            {
                "id": "99209065",
                "order": "99209059",
                "info": {
                    "price": "7.80",
                    "amount": "0.001283",
                    "timestamp": 1530062782,
                    "timestampms": 1530062782395,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0000250185",
                    "tid": 99209065,
                    "order_id": "99209059",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530062784769"
                },
                "timestamp": 1530062782395,
                "datetime": "2018-06-27T01: 26: 22.395Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 7.8,
                "cost": 0.0100074,
                "amount": 0.001283,
                "fee": {
                    "cost": 2.50185e-05,
                    "currency": "USD"
                }
            },
            {
                "id": "99209063",
                "order": "99209059",
                "info": {
                    "price": "7.81",
                    "amount": "0.005128",
                    "timestamp": 1530062782,
                    "timestampms": 1530062782395,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0001001242",
                    "tid": 99209063,
                    "order_id": "99209059",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530062784769"
                },
                "timestamp": 1530062782395,
                "datetime": "2018-06-27T01: 26: 22.395Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 7.81,
                "cost": 0.04004968,
                "amount": 0.005128,
                "fee": {
                    "cost": 0.0001001242,
                    "currency": "USD"
                }
            },
            {
                "id": "99209061",
                "order": "99209059",
                "info": {
                    "price": "7.81",
                    "amount": "0.001282",
                    "timestamp": 1530062782,
                    "timestampms": 1530062782395,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.00002503105",
                    "tid": 99209061,
                    "order_id": "99209059",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530062784769"
                },
                "timestamp": 1530062782395,
                "datetime": "2018-06-27T01: 26: 22.395Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 7.81,
                "cost": 0.01001242,
                "amount": 0.001282,
                "fee": {
                    "cost": 2.503105e-05,
                    "currency": "USD"
                }
            },
            {
                "id": "99210130",
                "order": "99210126",
                "info": {
                    "price": "175.00",
                    "amount": "0.3",
                    "timestamp": 1530090722,
                    "timestampms": 1530090722133,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.13125",
                    "tid": 99210130,
                    "order_id": "99210126",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530090722531"
                },
                "timestamp": 1530090722133,
                "datetime": "2018-06-27T09: 12: 02.133Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 175.0,
                "cost": 52.5,
                "amount": 0.3,
                "fee": {
                    "cost": 0.13125,
                    "currency": "USD"
                }
            },
            {
                "id": "99210128",
                "order": "99210126",
                "info": {
                    "price": "180.91",
                    "amount": "0.2",
                    "timestamp": 1530090722,
                    "timestampms": 1530090722133,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.090455",
                    "tid": 99210128,
                    "order_id": "99210126",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530090722531"
                },
                "timestamp": 1530090722133,
                "datetime": "2018-06-27T09: 12: 02.133Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 180.91,
                "cost": 36.182,
                "amount": 0.2,
                "fee": {
                    "cost": 0.090455,
                    "currency": "USD"
                }
            },
            {
                "id": "99210256",
                "order": "99210252",
                "info": {
                    "price": "180.00",
                    "amount": "0.1",
                    "timestamp": 1530092517,
                    "timestampms": 1530092517717,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.045",
                    "tid": 99210256,
                    "order_id": "99210252",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530092518169"
                },
                "timestamp": 1530092517717,
                "datetime": "2018-06-27T09: 41: 58.717Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 180.0,
                "cost": 18.0,
                "amount": 0.1,
                "fee": {
                    "cost": 0.045,
                    "currency": "USD"
                }
            },
            {
                "id": "99210254",
                "order": "99210252",
                "info": {
                    "price": "179.00",
                    "amount": "0.2",
                    "timestamp": 1530092517,
                    "timestampms": 1530092517717,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0895",
                    "tid": 99210254,
                    "order_id": "99210252",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530092518169"
                },
                "timestamp": 1530092517717,
                "datetime": "2018-06-27T09: 41: 58.717Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 179.0,
                "cost": 35.800000000000004,
                "amount": 0.2,
                "fee": {
                    "cost": 0.0895,
                    "currency": "USD"
                }
            }
        ]
    },
    {
        'create_order': {
            "info": {
                "order_id": "99210252",
                "id": "99210252",
                "symbol": "ethusd",
                "exchange": "gemini",
                "avg_execution_price": "179.3333333333333333333333333333333",
                "side": "buy",
                "type": "exchange limit",
                "timestamp": "1530092517",
                "timestampms": 1530092517716,
                "is_live": False,
                "is_cancelled": False,
                "is_hidden": False,
                "was_forced": False,
                "executed_amount": "0.3",
                "remaining_amount": "0",
                "client_order_id": "1530092518169",
                "options": [
                    "immediate-or-cancel"
                ],
                "price": "200.00",
                "original_amount": "0.3"
            },
            "id": "99210252"
        },
        'fetch_my_trades': [
            {
                "id": "99210256",
                "order": "99210252",
                "info": {
                    "price": "180.00",
                    "amount": "0.1",
                    "timestamp": 1530092517,
                    "timestampms": 1530092517717,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.045",
                    "tid": 99210256,
                    "order_id": "99210252",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530092518169"
                },
                "timestamp": 1530092517717,
                "datetime": "2018-06-27T09: 41: 58.717Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 180.0,
                "cost": 18.0,
                "amount": 0.1,
                "fee": {
                    "cost": 0.045,
                    "currency": "USD"
                }
            },
            {
                "id": "99210254",
                "order": "99210252",
                "info": {
                    "price": "179.00",
                    "amount": "0.2",
                    "timestamp": 1530092517,
                    "timestampms": 1530092517717,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0895",
                    "tid": 99210254,
                    "order_id": "99210252",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530092518169"
                },
                "timestamp": 1530092517717,
                "datetime": "2018-06-27T09: 41: 58.717Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 179.0,
                "cost": 35.800000000000004,
                "amount": 0.2,
                "fee": {
                    "cost": 0.0895,
                    "currency": "USD"
                }
            }
        ]
    },
    {
        'create_order': {
            "info": {
                "order_id": "987654321",
                "id": "987654321",
                "symbol": "ethusd",
                "exchange": "gemini",
                "avg_execution_price": "0",
                "side": "buy",
                "type": "exchange limit",
                "timestamp": "1530092517",
                "timestampms": 1530092517716,
                "is_live": False,
                "is_cancelled": False,
                "is_hidden": False,
                "was_forced": False,
                "executed_amount": "0",
                "remaining_amount": "0",
                "client_order_id": "1530092518169",
                "options": [
                    "immediate-or-cancel"
                ],
                "price": "200.00",
                "original_amount": "0"
            },
            "id": "987654321"
        },
        'fetch_my_trades': [
            {
                "id": "99210256",
                "order": "987654321",
                "info": {
                    "price": "180.00",
                    "amount": "0",
                    "timestamp": 1530092517,
                    "timestampms": 1530092517717,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.045",
                    "tid": 99210256,
                    "order_id": "987654321",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530092518169"
                },
                "timestamp": 1530092517717,
                "datetime": "2018-06-27T09: 41: 58.717Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 180.0,
                "cost": 0,
                "amount": 0,
                "fee": {
                    "cost": 0,
                    "currency": "USD"
                }
            }
        ]
    }
]

SELL_RESPONSES = [
    {
        'create_order': {
            "info": {
                "order_id": "97546903",
                "id": "97546903",
                "symbol": "ethusd",
                "exchange": "gemini",
                "avg_execution_price": "394.10",
                "side": "sell",
                "type": "exchange limit",
                "timestamp": "1529616497",
                "timestampms": 1529616497632,
                "is_live": False,
                "is_cancelled": False,
                "is_hidden": False,
                "was_forced": False,
                "executed_amount": "0.001",
                "remaining_amount": "0",
                "client_order_id": "1529616491439",
                "options": [
                    "immediate-or-cancel"
                ],
                "price": "388.00",
                "original_amount": "0.001"
            },
            "id": "97546903"
        },
        'fetch_my_trades': [
            {
                "id": "97546905",
                "order": "97546903",
                "info": {
                    "price": "394.10",
                    "amount": "0.001",
                    "timestamp": 1529616497,
                    "timestampms": 1529616497632,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.00098525",
                    "tid": 97546905,
                    "order_id": "97546903",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1529616491439"
                },
                "timestamp": 1529616497632,
                "datetime": "2018-06-21T21: 28: 18.632Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 394.1,
                "cost": 0.3941,
                "amount": 0.001,
                "fee": {
                    "cost": 0.00098525,
                    "currency": "USD"
                }
            }
        ]
    },
    {
        'create_order': {
            "info": {
                "order_id": "99210126",
                "id": "99210126",
                "symbol": "ethusd",
                "exchange": "gemini",
                "avg_execution_price": "177.364",
                "side": "sell",
                "type": "exchange limit",
                "timestamp": "1530090722",
                "timestampms": 1530090722132,
                "is_live": False,
                "is_cancelled": False,
                "is_hidden": False,
                "was_forced": False,
                "executed_amount": "0.5",
                "remaining_amount": "0",
                "client_order_id": "1530090722531",
                "options": [
                    "immediate-or-cancel"
                ],
                "price": "150.00",
                "original_amount": "0.5"
            },
            "id": "99210126"
        },
        'fetch_my_trades': [
            {
                "id": "93023095",
                "order": "93023093",
                "info": {
                    "price": "37.48",
                    "amount": "1",
                    "timestamp": 1522374592,
                    "timestampms": 1522374592522,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0937",
                    "tid": 93023095,
                    "order_id": "93023093",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1522374592"
                },
                "timestamp": 1522374592522,
                "datetime": "2018-03-30T01: 49: 53.522Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 37.48,
                "cost": 37.48,
                "amount": 1.0,
                "fee": {
                    "cost": 0.0937,
                    "currency": "USD"
                }
            },
            {
                "id": "93023113",
                "order": "93023111",
                "info": {
                    "price": "37.48",
                    "amount": "1",
                    "timestamp": 1522374785,
                    "timestampms": 1522374785789,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0937",
                    "tid": 93023113,
                    "order_id": "93023111",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1522374786"
                },
                "timestamp": 1522374785789,
                "datetime": "2018-03-30T01: 53: 06.789Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 37.48,
                "cost": 37.48,
                "amount": 1.0,
                "fee": {
                    "cost": 0.0937,
                    "currency": "USD"
                }
            },
            {
                "id": "93024394",
                "order": "93024392",
                "info": {
                    "price": "37.48",
                    "amount": "0.5",
                    "timestamp": 1522395847,
                    "timestampms": 1522395847069,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.04685",
                    "tid": 93024394,
                    "order_id": "93024392",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1522395847"
                },
                "timestamp": 1522395847069,
                "datetime": "2018-03-30T07: 44: 07.690Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 37.48,
                "cost": 18.74,
                "amount": 0.5,
                "fee": {
                    "cost": 0.04685,
                    "currency": "USD"
                }
            },
            {
                "id": "93565883",
                "order": "93565881",
                "info": {
                    "price": "222.00",
                    "amount": "0.022523",
                    "timestamp": 1523781354,
                    "timestampms": 1523781354442,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500265",
                    "tid": 93565883,
                    "order_id": "93565881",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1523781355"
                },
                "timestamp": 1523781354442,
                "datetime": "2018-04-15T08: 35: 54.442Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 222.0,
                "cost": 5.000106000000001,
                "amount": 0.022523,
                "fee": {
                    "cost": 0.012500265,
                    "currency": "USD"
                }
            },
            {
                "id": "93817225",
                "order": "93817223",
                "info": {
                    "price": "450.00",
                    "amount": "0.011111",
                    "timestamp": 1523993651,
                    "timestampms": 1523993651053,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012499875",
                    "tid": 93817225,
                    "order_id": "93817223",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1523993653"
                },
                "timestamp": 1523993651053,
                "datetime": "2018-04-17T19: 34: 11.530Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 450.0,
                "cost": 4.99995,
                "amount": 0.011111,
                "fee": {
                    "cost": 0.012499875,
                    "currency": "USD"
                }
            },
            {
                "id": "93860188",
                "order": "93860186",
                "info": {
                    "price": "450.00",
                    "amount": "0.011111",
                    "timestamp": 1523994779,
                    "timestampms": 1523994779522,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012499875",
                    "tid": 93860188,
                    "order_id": "93860186",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1523994781"
                },
                "timestamp": 1523994779522,
                "datetime": "2018-04-17T19: 53: 00.522Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 450.0,
                "cost": 4.99995,
                "amount": 0.011111,
                "fee": {
                    "cost": 0.012499875,
                    "currency": "USD"
                }
            },
            {
                "id": "93891062",
                "order": "93891060",
                "info": {
                    "price": "450.00",
                    "amount": "0.011111",
                    "timestamp": 1524008814,
                    "timestampms": 1524008814271,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012499875",
                    "tid": 93891062,
                    "order_id": "93891060",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524008816"
                },
                "timestamp": 1524008814271,
                "datetime": "2018-04-17T23: 46: 54.271Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 450.0,
                "cost": 4.99995,
                "amount": 0.011111,
                "fee": {
                    "cost": 0.012499875,
                    "currency": "USD"
                }
            },
            {
                "id": "93891299",
                "order": "93891297",
                "info": {
                    "price": "450.00",
                    "amount": "0.011111",
                    "timestamp": 1524015070,
                    "timestampms": 1524015070735,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012499875",
                    "tid": 93891299,
                    "order_id": "93891297",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524015070"
                },
                "timestamp": 1524015070735,
                "datetime": "2018-04-18T01: 31: 11.735Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 450.0,
                "cost": 4.99995,
                "amount": 0.011111,
                "fee": {
                    "cost": 0.012499875,
                    "currency": "USD"
                }
            },
            {
                "id": "93891312",
                "order": "93891310",
                "info": {
                    "price": "450.00",
                    "amount": "0.011111",
                    "timestamp": 1524015342,
                    "timestampms": 1524015342226,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012499875",
                    "tid": 93891312,
                    "order_id": "93891310",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524015342"
                },
                "timestamp": 1524015342226,
                "datetime": "2018-04-18T01: 35: 42.226Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 450.0,
                "cost": 4.99995,
                "amount": 0.011111,
                "fee": {
                    "cost": 0.012499875,
                    "currency": "USD"
                }
            },
            {
                "id": "94272781",
                "order": "94272779",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524197468,
                    "timestampms": 1524197468933,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94272781,
                    "order_id": "94272779",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524197468"
                },
                "timestamp": 1524197468933,
                "datetime": "2018-04-20T04: 11: 09.933Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94272810",
                "order": "94272808",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524197713,
                    "timestampms": 1524197713327,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94272810,
                    "order_id": "94272808",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524197713"
                },
                "timestamp": 1524197713327,
                "datetime": "2018-04-20T04: 15: 13.327Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94272881",
                "order": "94272879",
                "info": {
                    "price": "99.48",
                    "amount": "0.050261",
                    "timestamp": 1524198343,
                    "timestampms": 1524198343466,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0124999107",
                    "tid": 94272881,
                    "order_id": "94272879",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524198343"
                },
                "timestamp": 1524198343466,
                "datetime": "2018-04-20T04: 25: 43.466Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 99.48,
                "cost": 4.99996428,
                "amount": 0.050261,
                "fee": {
                    "cost": 0.0124999107,
                    "currency": "USD"
                }
            },
            {
                "id": "94272927",
                "order": "94272925",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524198446,
                    "timestampms": 1524198446293,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94272927,
                    "order_id": "94272925",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524198446"
                },
                "timestamp": 1524198446293,
                "datetime": "2018-04-20T04: 27: 26.293Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94272958",
                "order": "94272956",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524198857,
                    "timestampms": 1524198857521,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94272958,
                    "order_id": "94272956",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524198857"
                },
                "timestamp": 1524198857521,
                "datetime": "2018-04-20T04: 34: 18.521Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94273367",
                "order": "94273365",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524204632,
                    "timestampms": 1524204632400,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94273367,
                    "order_id": "94273365",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524204632"
                },
                "timestamp": 1524204632400,
                "datetime": "2018-04-20T06: 10: 32.400Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94273386",
                "order": "94273384",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524205024,
                    "timestampms": 1524205024905,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94273386,
                    "order_id": "94273384",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524205024"
                },
                "timestamp": 1524205024905,
                "datetime": "2018-04-20T06: 17: 05.905Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94273397",
                "order": "94273395",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524205218,
                    "timestampms": 1524205218956,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94273397,
                    "order_id": "94273395",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524205218"
                },
                "timestamp": 1524205218956,
                "datetime": "2018-04-20T06: 20: 19.956Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94343771",
                "order": "94343769",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524432181,
                    "timestampms": 1524432181599,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94343771,
                    "order_id": "94343769",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524432179"
                },
                "timestamp": 1524432181599,
                "datetime": "2018-04-22T21: 23: 02.599Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94343776",
                "order": "94343774",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524432211,
                    "timestampms": 1524432211593,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94343776,
                    "order_id": "94343774",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524432211"
                },
                "timestamp": 1524432211593,
                "datetime": "2018-04-22T21: 23: 32.593Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94437307",
                "order": "94437305",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524524300,
                    "timestampms": 1524524300380,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94437307,
                    "order_id": "94437305",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524524300085"
                },
                "timestamp": 1524524300380,
                "datetime": "2018-04-23T22: 58: 20.380Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94445024",
                "order": "94445022",
                "info": {
                    "price": "397.00",
                    "amount": "0.012594",
                    "timestamp": 1524633587,
                    "timestampms": 1524633587235,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012499545",
                    "tid": 94445024,
                    "order_id": "94445022",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524633587162"
                },
                "timestamp": 1524633587235,
                "datetime": "2018-04-25T05: 19: 47.235Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 397.0,
                "cost": 4.999817999999999,
                "amount": 0.012594,
                "fee": {
                    "cost": 0.012499545,
                    "currency": "USD"
                }
            },
            {
                "id": "94445366",
                "order": "94445364",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524638635,
                    "timestampms": 1524638635333,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94445366,
                    "order_id": "94445364",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524638635042"
                },
                "timestamp": 1524638635333,
                "datetime": "2018-04-25T06: 43: 55.333Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94445597",
                "order": "94445595",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524644893,
                    "timestampms": 1524644893657,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94445597,
                    "order_id": "94445595",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524644893331"
                },
                "timestamp": 1524644893657,
                "datetime": "2018-04-25T08: 28: 14.657Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94445602",
                "order": "94445600",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1524644907,
                    "timestampms": 1524644907794,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94445602,
                    "order_id": "94445600",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1524644907468"
                },
                "timestamp": 1524644907794,
                "datetime": "2018-04-25T08: 28: 28.794Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94527341",
                "order": "94527339",
                "info": {
                    "price": "398.00",
                    "amount": "0.012563",
                    "timestamp": 1525242567,
                    "timestampms": 1525242567776,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.012500185",
                    "tid": 94527341,
                    "order_id": "94527339",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1525242567687"
                },
                "timestamp": 1525242567776,
                "datetime": "2018-05-02T06: 29: 28.776Z",
                "symbol": "ETH/USD",
                "type":
                None,
                "side": "Buy",
                "price": 398.0,
                "cost": 5.000074,
                "amount": 0.012563,
                "fee": {
                    "cost": 0.012500185,
                    "currency": "USD"
                }
            },
            {
                "id": "94616276",
                "order": "94616274",
                "info": {
                    "price": "398.00",
                    "amount": "0.012562",
                    "timestamp": 1526183096,
                    "timestampms": 1526183096513,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.01249919",
                    "tid": 94616276,
                    "order_id": "94616274",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1526183096427"
                },
                "timestamp": 1526183096513,
                "datetime": "2018-05-13T03: 44: 57.513Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 4.999676,
                "amount": 0.012562,
                "fee": {
                    "cost": 0.01249919,
                    "currency": "USD"
                }
            },
            {
                "id": "97546905",
                "order": "97546903",
                "info": {
                    "price": "394.10",
                    "amount": "0.001",
                    "timestamp": 1529616497,
                    "timestampms": 1529616497632,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.00098525",
                    "tid": 97546905,
                    "order_id": "97546903",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1529616491439"
                },
                "timestamp": 1529616497632,
                "datetime": "2018-06-21T21: 28: 18.632Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 394.1,
                "cost": 0.3941,
                "amount": 0.001,
                "fee": {
                    "cost": 0.00098525,
                    "currency": "USD"
                }
            },
            {
                "id": "97580677",
                "order": "97580675",
                "info": {
                    "price": "398.00",
                    "amount": "0.1",
                    "timestamp": 1529617177,
                    "timestampms": 1529617177985,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0995",
                    "tid": 97580677,
                    "order_id": "97580675",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1529617171779"
                },
                "timestamp": 1529617177985,
                "datetime": "2018-06-21T21: 39: 38.985Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 39.800000000000004,
                "amount": 0.1,
                "fee": {
                    "cost": 0.0995,
                    "currency": "USD"
                }
            },
            {
                "id": "97866234",
                "order": "97866232",
                "info": {
                    "price": "394.10",
                    "amount": "0.001",
                    "timestamp": 1529623001,
                    "timestampms": 1529623001878,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.00098525",
                    "tid": 97866234,
                    "order_id": "97866232",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1529623001793"
                },
                "timestamp": 1529623001878,
                "datetime": "2018-06-21T23: 16: 42.878Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 394.1,
                "cost": 0.3941,
                "amount": 0.001,
                "fee": {
                    "cost": 0.00098525,
                    "currency": "USD"
                }
            },
            {
                "id": "97869134",
                "order": "97869132",
                "info": {
                    "price": "394.10",
                    "amount": "0.001",
                    "timestamp": 1529623046,
                    "timestampms": 1529623046764,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.00098525",
                    "tid": 97869134,
                    "order_id": "97869132",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1529623043770"
                },
                "timestamp": 1529623046764,
                "datetime": "2018-06-21T23: 17: 27.764Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 394.1,
                "cost": 0.3941,
                "amount": 0.001,
                "fee": {
                    "cost": 0.00098525,
                    "currency": "USD"
                }
            },
            {
                "id": "98645283",
                "order": "98645281",
                "info": {
                    "price": "398.00",
                    "amount": "0.1",
                    "timestamp": 1529647877,
                    "timestampms": 1529647877854,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0995",
                    "tid": 98645283,
                    "order_id": "98645281",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1529647877508"
                },
                "timestamp": 1529647877854,
                "datetime": "2018-06-22T06: 11: 18.854Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 39.800000000000004,
                "amount": 0.1,
                "fee": {
                    "cost": 0.0995,
                    "currency": "USD"
                }
            },
            {
                "id": "98645699",
                "order": "98645697",
                "info": {
                    "price": "398.00",
                    "amount": "0.1",
                    "timestamp": 1529647902,
                    "timestampms": 1529647902534,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0995",
                    "tid": 98645699,
                    "order_id": "98645697",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1529647902187"
                },
                "timestamp": 1529647902534,
                "datetime": "2018-06-22T06: 11: 43.534Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 39.800000000000004,
                "amount": 0.1,
                "fee": {
                    "cost": 0.0995,
                    "currency": "USD"
                }
            },
            {
                "id": "98654969",
                "order": "98654967",
                "info": {
                    "price": "398.00",
                    "amount": "0.1",
                    "timestamp": 1529648466,
                    "timestampms": 1529648466481,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0995",
                    "tid": 98654969,
                    "order_id": "98654967",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1529648466127"
                },
                "timestamp": 1529648466481,
                "datetime": "2018-06-22T06: 21: 06.481Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 39.800000000000004,
                "amount": 0.1,
                "fee": {
                    "cost": 0.0995,
                    "currency": "USD"
                }
            },
            {
                "id": "98655124",
                "order": "98655120",
                "info": {
                    "price": "398.00",
                    "amount": "0.1",
                    "timestamp": 1529648478,
                    "timestampms": 1529648478948,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0995",
                    "tid": 98655124,
                    "order_id": "98655120",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1529648478595"
                },
                "timestamp": 1529648478948,
                "datetime": "2018-06-22T06: 21: 19.948Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 39.800000000000004,
                "amount": 0.1,
                "fee": {
                    "cost": 0.0995,
                    "currency": "USD"
                }
            },
            {
                "id": "98659625",
                "order": "98659623",
                "info": {
                    "price": "398.00",
                    "amount": "0.1",
                    "timestamp": 1529648756,
                    "timestampms": 1529648756216,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0995",
                    "tid": 98659625,
                    "order_id": "98659623",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1529648755867"
                },
                "timestamp": 1529648756216,
                "datetime": "2018-06-22T06: 25: 56.216Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 398.0,
                "cost": 39.800000000000004,
                "amount": 0.1,
                "fee": {
                    "cost": 0.0995,
                    "currency": "USD"
                }
            },
            {
                "id": "99208728",
                "order": "99208726",
                "info": {
                    "price": "181.91",
                    "amount": "0.01",
                    "timestamp": 1530055656,
                    "timestampms": 1530055656687,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.00454775",
                    "tid": 99208728,
                    "order_id": "99208726",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530055658856"
                },
                "timestamp": 1530055656687,
                "datetime": "2018-06-26T23: 27: 37.687Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 181.91,
                "cost": 1.8191,
                "amount": 0.01,
                "fee": {
                    "cost": 0.00454775,
                    "currency": "USD"
                }
            },
            {
                "id": "99208984",
                "order": "99208982",
                "info": {
                    "price": "181.91",
                    "amount": "0.01",
                    "timestamp": 1530061088,
                    "timestampms": 1530061088112,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.00454775",
                    "tid": 99208984,
                    "order_id": "99208982",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530061090427"
                },
                "timestamp": 1530061088112,
                "datetime": "2018-06-27T00: 58: 08.112Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 181.91,
                "cost": 1.8191,
                "amount": 0.01,
                "fee": {
                    "cost": 0.00454775,
                    "currency": "USD"
                }
            },
            {
                "id": "99209017",
                "order": "99209015",
                "info": {
                    "price": "181.91",
                    "amount": "0.01",
                    "timestamp": 1530061928,
                    "timestampms": 1530061928236,
                    "type": "Buy",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.00454775",
                    "tid": 99209017,
                    "order_id": "99209015",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530061930526"
                },
                "timestamp": 1530061928236,
                "datetime": "2018-06-27T01: 12: 08.236Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Buy",
                "price": 181.91,
                "cost": 1.8191,
                "amount": 0.01,
                "fee": {
                    "cost": 0.00454775,
                    "currency": "USD"
                }
            },
            {
                "id": "99209067",
                "order": "99209059",
                "info": {
                    "price": "7.80",
                    "amount": "0.002307",
                    "timestamp": 1530062782,
                    "timestampms": 1530062782395,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0000449865",
                    "tid": 99209067,
                    "order_id": "99209059",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530062784769"
                },
                "timestamp": 1530062782395,
                "datetime": "2018-06-27T01: 26: 22.395Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 7.8,
                "cost": 0.0179946,
                "amount": 0.002307,
                "fee": {
                    "cost": 4.49865e-05,
                    "currency": "USD"
                }
            },
            {
                "id": "99209065",
                "order": "99209059",
                "info": {
                    "price": "7.80",
                    "amount": "0.001283",
                    "timestamp": 1530062782,
                    "timestampms": 1530062782395,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0000250185",
                    "tid": 99209065,
                    "order_id": "99209059",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530062784769"
                },
                "timestamp": 1530062782395,
                "datetime": "2018-06-27T01: 26: 22.395Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 7.8,
                "cost": 0.0100074,
                "amount": 0.001283,
                "fee": {
                    "cost": 2.50185e-05,
                    "currency": "USD"
                }
            },
            {
                "id": "99209063",
                "order": "99209059",
                "info": {
                    "price": "7.81",
                    "amount": "0.005128",
                    "timestamp": 1530062782,
                    "timestampms": 1530062782395,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.0001001242",
                    "tid": 99209063,
                    "order_id": "99209059",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530062784769"
                },
                "timestamp": 1530062782395,
                "datetime": "2018-06-27T01: 26: 22.395Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 7.81,
                "cost": 0.04004968,
                "amount": 0.005128,
                "fee": {
                    "cost": 0.0001001242,
                    "currency": "USD"
                }
            },
            {
                "id": "99209061",
                "order": "99209059",
                "info": {
                    "price": "7.81",
                    "amount": "0.001282",
                    "timestamp": 1530062782,
                    "timestampms": 1530062782395,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.00002503105",
                    "tid": 99209061,
                    "order_id": "99209059",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530062784769"
                },
                "timestamp": 1530062782395,
                "datetime": "2018-06-27T01: 26: 22.395Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 7.81,
                "cost": 0.01001242,
                "amount": 0.001282,
                "fee": {
                    "cost": 2.503105e-05,
                    "currency": "USD"
                }
            },
            {
                "id": "99210130",
                "order": "99210126",
                "info": {
                    "price": "175.00",
                    "amount": "0.3",
                    "timestamp": 1530090722,
                    "timestampms": 1530090722133,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.13125",
                    "tid": 99210130,
                    "order_id": "99210126",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530090722531"
                },
                "timestamp": 1530090722133,
                "datetime": "2018-06-27T09: 12: 02.133Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 175.0,
                "cost": 52.5,
                "amount": 0.3,
                "fee": {
                    "cost": 0.13125,
                    "currency": "USD"
                }
            },
            {
                "id": "99210128",
                "order": "99210126",
                "info": {
                    "price": "180.91",
                    "amount": "0.2",
                    "timestamp": 1530090722,
                    "timestampms": 1530090722133,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.090455",
                    "tid": 99210128,
                    "order_id": "99210126",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530090722531"
                },
                "timestamp": 1530090722133,
                "datetime": "2018-06-27T09: 12: 02.133Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 180.91,
                "cost": 36.182,
                "amount": 0.2,
                "fee": {
                    "cost": 0.090455,
                    "currency": "USD"
                }
            }
        ]
    },
    {
        'create_order': {
            "info": {
                "order_id": "99210126",
                "id": "99210126",
                "symbol": "ethusd",
                "exchange": "gemini",
                "avg_execution_price": "177.364",
                "side": "sell",
                "type": "exchange limit",
                "timestamp": "1530090722",
                "timestampms": 1530090722132,
                "is_live": False,
                "is_cancelled": False,
                "is_hidden": False,
                "was_forced": False,
                "executed_amount": "0.5",
                "remaining_amount": "0",
                "client_order_id": "1530090722531",
                "options": [
                    "immediate-or-cancel"
                ],
                "price": "150.00",
                "original_amount": "0.5"
            },
            "id": "99210126"
        },
        'fetch_my_trades': [
            {
                "id": "99210130",
                "order": "99210126",
                "info": {
                    "price": "175.00",
                    "amount": "0.3",
                    "timestamp": 1530090722,
                    "timestampms": 1530090722133,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.13125",
                    "tid": 99210130,
                    "order_id": "99210126",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530090722531"
                },
                "timestamp": 1530090722133,
                "datetime": "2018-06-27T09: 12: 02.133Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 175.0,
                "cost": 52.5,
                "amount": 0.3,
                "fee": {
                    "cost": 0.13125,
                    "currency": "USD"
                }
            },
            {
                "id": "99210128",
                "order": "99210126",
                "info": {
                    "price": "180.91",
                    "amount": "0.2",
                    "timestamp": 1530090722,
                    "timestampms": 1530090722133,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0.090455",
                    "tid": 99210128,
                    "order_id": "99210126",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530090722531"
                },
                "timestamp": 1530090722133,
                "datetime": "2018-06-27T09: 12: 02.133Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 180.91,
                "cost": 36.182,
                "amount": 0.2,
                "fee": {
                    "cost": 0.090455,
                    "currency": "USD"
                }
            }
        ]
    },
    {
        'create_order': {
            "info": {
                "order_id": "123456789",
                "id": "123456789",
                "symbol": "ethusd",
                "exchange": "gemini",
                "avg_execution_price": "0",
                "side": "sell",
                "type": "exchange limit",
                "timestamp": "1530090722",
                "timestampms": 1530090722132,
                "is_live": False,
                "is_cancelled": False,
                "is_hidden": False,
                "was_forced": False,
                "executed_amount": "0",
                "remaining_amount": "0",
                "client_order_id": "1530090722531",
                "options": [
                    "immediate-or-cancel"
                ],
                "price": "150.00",
                "original_amount": "0"
            },
            "id": "123456789"
        },
        'fetch_my_trades': [
            {
                "id": "99210130",
                "order": "123456789",
                "info": {
                    "price": "175.00",
                    "amount": "0",
                    "timestamp": 1530090722,
                    "timestampms": 1530090722133,
                    "type": "Sell",
                    "aggressor": True,
                    "fee_currency": "USD",
                    "fee_amount": "0",
                    "tid": 99210130,
                    "order_id": "123456789",
                    "exchange": "gemini",
                    "is_auction_fill": False,
                    "client_order_id": "1530090722531"
                },
                "timestamp": 1530090722133,
                "datetime": "2018-06-27T09: 12: 02.133Z",
                "symbol": "ETH/USD",
                "type": None,
                "side": "Sell",
                "price": 175.0,
                "cost": 0,
                "amount": 0,
                "fee": {
                    "cost": 0,
                    "currency": "USD"
                }
            }
        ]
    }
]

BUY_RESULTS = [
    {
        'pre_fee_base': Decimal('0.1'),
        'pre_fee_quote': Decimal('39.800000000000004'),
        'post_fee_base': Decimal('0.1'),
        'post_fee_quote': Decimal('39.899500000000004'),
        'fees': Decimal('0.0995'),
        'fee_asset': 'USD',
        'price': Decimal('398.00000000000004'),
        'true_price': Decimal('398.99500000000004'),
        'side': 'buy',
        'type': 'limit',
        'order_id': '97580675',
        'exchange_timestamp': 1529617177,
        'extra_info': {"options": ["immediate-or-cancel"]}
    },
    {
        'pre_fee_base': Decimal('0.3'),
        'pre_fee_quote': Decimal('53.800000000000004'),
        'post_fee_base': Decimal('0.3'),
        'post_fee_quote': Decimal('53.934500000000004'),
        'fees': Decimal('0.1345'),
        'fee_asset': 'USD',
        'price': Decimal('179.3333333333333466666666667'),
        'true_price': Decimal('179.78166666666668'),
        'side': 'buy',
        'type': 'limit',
        'order_id': '99210252',
        'exchange_timestamp': 1530092517,
        'extra_info': {"options": ["immediate-or-cancel"]}
    },
    {
        'pre_fee_base': Decimal('0.3'),
        'pre_fee_quote': Decimal('53.800000000000004'),
        'post_fee_base': Decimal('0.3'),
        'post_fee_quote': Decimal('53.934500000000004'),
        'fees': Decimal('0.1345'),
        'fee_asset': 'USD',
        'price': Decimal('179.3333333333333466666666667'),
        'true_price': Decimal('179.78166666666668'),
        'side': 'buy',
        'type': 'limit',
        'order_id': '99210252',
        'exchange_timestamp': 1530092517,
        'extra_info': {"options": ["immediate-or-cancel"]}
    },
    {
        'pre_fee_base': Decimal('0'),
        'pre_fee_quote': Decimal('0'),
        'post_fee_base': Decimal('0'),
        'post_fee_quote': Decimal('0'),
        'fees': Decimal('0'),
        'fee_asset': 'USD',
        'price': Decimal('0'),
        'true_price': Decimal('0'),
        'side': 'buy',
        'type': 'limit',
        'order_id': '987654321',
        'exchange_timestamp': 1530092517,
        'extra_info': {"options": ["immediate-or-cancel"]}
    }
]

SELL_RESULTS = [
    {
        'pre_fee_base': Decimal('0.001'),
        'pre_fee_quote': Decimal('0.3941'),
        'post_fee_base': Decimal('0.001'),
        'post_fee_quote': Decimal('0.39311475'),
        'fees': Decimal('0.00098525'),
        'fee_asset': 'USD',
        'price': Decimal('394.1'),
        'true_price': Decimal('393.11475'),
        'side': 'sell',
        'type': 'limit',
        'order_id': '97546903',
        'exchange_timestamp': 1529616497,
        'extra_info': {"options": ["immediate-or-cancel"]}
    },
    {
        'pre_fee_base': Decimal('0.5'),
        'pre_fee_quote': Decimal('88.682'),
        'post_fee_base': Decimal('0.5'),
        'post_fee_quote': Decimal('88.460295'),
        'fees': Decimal('0.221705'),
        'fee_asset': 'USD',
        'price': Decimal('177.364'),
        'true_price': Decimal('176.92059'),
        'side': 'sell',
        'type': 'limit',
        'order_id': '99210126',
        'exchange_timestamp': 1530090722,
        'extra_info': {"options": ["immediate-or-cancel"]}
    },
    {
        'pre_fee_base': Decimal('0.5'),
        'pre_fee_quote': Decimal('88.682'),
        'post_fee_base': Decimal('0.5'),
        'post_fee_quote': Decimal('88.460295'),
        'fees': Decimal('0.221705'),
        'fee_asset': 'USD',
        'price': Decimal('177.364'),
        'true_price': Decimal('176.92059'),
        'side': 'sell',
        'type': 'limit',
        'order_id': '99210126',
        'exchange_timestamp': 1530090722,
        'extra_info': {"options": ["immediate-or-cancel"]}
    },
    {
        'pre_fee_base': Decimal('0'),
        'pre_fee_quote': Decimal('0'),
        'post_fee_base': Decimal('0'),
        'post_fee_quote': Decimal('0'),
        'fees': Decimal('0'),
        'fee_asset': 'USD',
        'price': Decimal('0'),
        'true_price': Decimal('0'),
        'side': 'sell',
        'type': 'limit',
        'order_id': '123456789',
        'exchange_timestamp': 1530090722,
        'extra_info': {"options": ["immediate-or-cancel"]}
    }
]
