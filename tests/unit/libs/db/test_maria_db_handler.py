# pylint: disable=E1101
from collections import namedtuple
from unittest.mock import MagicMock

import MySQLdb
import pytest

import libs.db.maria_db_handler as db_handler
from libs.db.maria_db_handler import InvalidRowFormatError

xfail = pytest.mark.xfail

InvalidRowNamedTuple = namedtuple("InvalidRowNamedTuple", ['data1', 'data2', 'data3'])
FAKE_ROW_NAMED_TUPLE = InvalidRowNamedTuple('some', 'fake', 'data')
FAKE_ROW_MAP = {
    'column1': 'data1',
    'column2': 'data2',
    'column3': 'data3',
    'column4': 'data4',
    'column5': 'data5',
}
FAKE_ROW_MAP_COLUMNS = *FAKE_ROW_MAP,
FAKE_ROW_MAP_ROW_DATA = *FAKE_ROW_MAP.values(),
FAKE_ROW_MAP_PARAMS = '%s, %s, %s, %s, %s'
FAKE_TABLE_NAME = 'FAKE_TABLE_NAME'


@pytest.fixture(autouse=True)
def cleanup_db():
    db_handler.db = None

class MockMariaDB:
    def connect(self):
        return MagicMock()

@pytest.mark.parametrize('table_name, columns, param_string, expected_query', [
    ('sample_table_name', ('column1', 'column2'), '%s, %s',
        'INSERT IGNORE INTO sample_table_name(column1, column2) VALUES (%s, %s)'),
    ('sample_table_name_deux', ("column1", "column2"), '%s, %s',
        'INSERT IGNORE INTO sample_table_name_deux(column1, column2) VALUES (%s, %s)'),
    ('cr@z33_t@bl3', ('#4389%$&#', '^&*())_+)*/\\'), '%s, %s',
        'INSERT IGNORE INTO cr@z33_t@bl3(#4389%$&#, ^&*())_+)*/\\\\) VALUES (%s, %s)'),
    ('RidicCoin_table', ("ridic's column1", "ridic's column2", "ridic's column3"), '%s, %s, %s',
        'INSERT IGNORE INTO RidicCoin_table(ridic\'s column1, ridic\'s column2, ridic\'s column3) VALUES (%s, %s, %s)')
])
def test_form_insert_ignore_query(table_name, columns, param_string, expected_query):
    query = db_handler._form_insert_ignore_query(table_name, columns, param_string)
    assert query == expected_query


@pytest.mark.parametrize('table_columns, exp_result', [
    ([], {}),
    (['column1', 'column2'], {
        'column1': 'data1',
        'column2': 'data2'
    }),
    pytest.param(['mangled_column1', 'mangled_column2'], {}, marks=xfail(
        raises=KeyError, reason="table_columns must exist in map_data", strict=True)),
    (['column1', 'column2', 'column3', 'column4', 'column5'], FAKE_ROW_MAP)
])
def test_build_row(table_columns, exp_result):
    result = db_handler.build_row(table_columns, FAKE_ROW_MAP)
    assert result == exp_result

def test_commit_all(mocker):
    db_handler.db = MockMariaDB().connect()
    db_handler.commit_all()
    db_handler.db.commit.assert_called_once_with()


@pytest.mark.parametrize('row, exp_columns, exp_row_data, exp_params', [
    pytest.param({}, (), (), '', marks=xfail(
        raises=InvalidRowFormatError, reason="row must not be empty", strict=True)),
    pytest.param(FAKE_ROW_NAMED_TUPLE, (), (), '', marks=xfail(
        raises=InvalidRowFormatError, reason="row must be a dict", strict=True)),
    pytest.param(('some', 'tuple'), (), (), '', marks=xfail(
        raises=InvalidRowFormatError, reason="row must be a dict", strict=True)),
    pytest.param(['some', 'list'], (), (), '', marks=xfail(
        raises=InvalidRowFormatError, reason="row must be a dict", strict=True)),
    (FAKE_ROW_MAP, FAKE_ROW_MAP_COLUMNS, FAKE_ROW_MAP_ROW_DATA, FAKE_ROW_MAP_PARAMS)
])
def test_insert_row(mocker, row, exp_columns, exp_row_data, exp_params):
    mock_cursor = MagicMock()
    mock_query = MagicMock()
    db_handler.db = MockMariaDB().connect()

    mocker.patch.object(db_handler, '_form_insert_ignore_query', return_value=mock_query)
    mocker.patch.object(db_handler.db, 'cursor', return_value=mock_cursor)

    db_handler.insert_row(FAKE_TABLE_NAME, row)

    db_handler.db.cursor.assert_called_once_with()
    mock_cursor.execute.assert_called_once_with(mock_query, exp_row_data)
    db_handler._form_insert_ignore_query.assert_called_once_with(
        FAKE_TABLE_NAME, exp_columns, exp_params)
    mock_cursor.close.assert_called_once_with()


@pytest.mark.parametrize('db_started', [ True, False ])
def test_start_db(mocker, db_started):
    FAKE_USER = 'fake_user'
    FAKE_PASSWORD = 'fake_password'
    FAKE_DB_NAME = 'fake_name'

    if db_started:
        db_handler.db = MockMariaDB().connect()

    mocker.patch.object(MySQLdb, 'connect')
    db_handler.start_db(FAKE_USER, FAKE_PASSWORD, FAKE_DB_NAME)

    if db_started is False:
        MySQLdb.connect.assert_called_once_with(user=FAKE_USER, passwd=FAKE_PASSWORD, db=FAKE_DB_NAME)
    else:
        MySQLdb.connect.assert_not_called()
