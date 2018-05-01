# Testing
Start at the top level directory of the project (Autotrageur).
### To run all tests:
```python -m pytest```
### To run a particular file, add the file:
```python -m pytest tests/unit/libs/test_utilities.py```
### To run a particualr test of the file:
```python -m pytest tests/unit/libs/test_utilities.py::test_not_keys_exists```


# Code Coverage
## Example usage:
`python -m pytest --cov=libs  tests/unit/libs/fetcher`
Should produce something like:

```
---------- coverage: platform win32, python 3.6.4-final-0 -----------
Name                                       Stmts   Miss  Cover
--------------------------------------------------------------
libs\ccxt_extensions\__init__.py               2      2     0%
libs\ccxt_extensions\ext_bithumb.py           12     12     0%
libs\ccxt_extensions\ext_gemini.py            39     39     0%
libs\cryCompare\__init__.py                    0      0   100%
libs\cryCompare\history.py                    45     45     0%
libs\cryCompare\price.py                      92     92     0%
libs\csv\__init__.py                           0      0   100%
libs\csv\csvmaker.py                          18     18     0%
libs\email_client\__init__.py                  0      0   100%
libs\email_client\simple_email_client.py      24     24     0%
libs\security\__init__.py                      0      0   100%
libs\security\encryption.py                   15     15     0%
libs\trade\__init__.py                         0      0   100%
libs\trade\executor\__init__.py                0      0   100%
libs\trade\executor\base_executor.py          12     12     0%
libs\trade\executor\ccxt_executor.py          12     12     0%
libs\trade\executor\dryrun_executor.py        21     21     0%
libs\trade\fetcher\__init__.py                 0      0   100%
libs\trade\fetcher\ccxt_fetcher.py            26      4    85%
libs\trade\fetcher\history_fetcher.py         26     26     0%
libs\utilities.py                             39     39     0%
--------------------------------------------------------------
TOTAL                                        383    361     6%
```

## Better reporting

From:
http://pytest-cov.readthedocs.io/en/latest/reporting.html

`python -m pytest --cov-report html --cov=libs  tests/unit/libs` will produce an html report where each module is clickable.  And missing lines will be highlighted.

`python -m pytest --cov-report term-missing --cov=libs  tests/unit/libs` will show missing
line numbers in terminal.