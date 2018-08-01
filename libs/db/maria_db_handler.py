import re
from collections import namedtuple

import MySQLdb


# The database object.
db = None


class InvalidRowFormatError(Exception):
    """Thrown when a row object is deemed invalid for DB insertion (e.g. Wrong
    type, or empty)"""
    pass


# See https://stackoverflow.com/questions/1606436/adding-docstrings-to-namedtuples
class InsertRowObject(namedtuple(
        'InsertRowObject', ['table_name', 'row', 'prim_key_columns'])):
    """Encapsulates the data needed to insert a row into the database.

    The metadata and data required to perform a row insertion include:
        - a table name
        - a row of data represented as a dict type.
        - primary key columns represented as a tuple of strings.
    """
    __slots__ = ()


def _form_insert_query(table_name, columns, row_data_params, prim_keys):
    """Forms the completed 'INSERT INTO ...' query string.

    Utilizes regex to strip single quotes from the columns tuple string.  The
    query string contains an optional 'ON DUPLICATE KEY UPDATE ...' extension
    if primary keys are provided.

    Args:
        table_name (str): Name of the table to insert into.
        columns (tuple(str)): Column names represented as a tuple of strings.
        row_data_params (str): A param substitution string composed of repeating
            sequences of '%s' for data insertion.  E.g. '%s, %s, %s"
        prim_keys (tuple(str)): Any primary key columns of the supplied table,
            represented as a tuple. E.g. ('col1', 'col2')

    Returns:
        str: A completed 'INSERT INTO ...' query string ready for execution.
    """
    insert_query = _insert_into_with_values(
        table_name, columns, row_data_params)

    # Form redundant 'ON DUPLICATE KEY UPDATE ...' clause for 'ON CONFLICT DO
    # NOTHING' equivalent.
    return _on_duplicate_key_update(insert_query, prim_keys)


def _insert_into_with_values(table_name, columns, row_data_params):
    """Forms an 'INSERT INTO ... VALUES(...)' query string.

    Args:
        table_name (str): Name of the table to insert into.
        columns (tuple(str)): Column names represented as a tuple of strings.
        row_data_params (str): A param substitution string composed of repeating
            sequences of '%s' for data insertion.  E.g. '%s, %s, %s"

    Returns:
        str: A basic 'INSERT INTO ... VALUES(...)' query string.
    """
    return (
        "INSERT INTO "
        + table_name
        + re.sub(r"((?<=\()('|\"))"              # single quote, look-behind '('
                 r"|(('|\")(?=,))"               # single quote, look-ahead ','
                 r"|((?<=[^\S\r\n\t]|,)('|\"))"  # single quote, look-behind space character, or ','
                 r"|(('|\")(?=\)))",             # single quote, look-ahead ')'
                 '', str(columns))
        + " VALUES ("
        + row_data_params
        + ")"
    )


def _on_duplicate_key_update(insert_query, prim_keys):
    """Appends an 'ON DUPLICATE KEY UPDATE ...' clause to the query string.

    The `insert_query` string will return unchanged if there are no `prim_keys`.

    Args:
        insert_query (str): An existing 'INSERT INTO ...' query string.
        prim_keys (tuple(str)): A tuple of primary key column names.

    Returns:
        str: A completed 'INSERT INTO ...' query string with the appended
            'ON DUPLICATE KEY UPDATE ...' portion (if necessary).
    """
    if prim_keys:
        redundant_update_prim_keys = ', '.join(
            "{} = {}".format(key, key) for key in prim_keys)

        insert_query += (
            " ON DUPLICATE KEY UPDATE "
            + redundant_update_prim_keys)

    return insert_query


def build_row(table_columns, map_data):
    """Builds a row designated for the table columns provided.

    Extracts the necessary keys from `map_data` and returns a newly formed map
    which represents the row data to be inserted into the table.

    Args:
        table_columns (list): A list of column names for the row to be built
            against.
        map_data (dict): The map to be filtered by `table_columns`.

    Returns:
        dict: A row object represented as a map with the filtered entries for
            `table_columns`.
    """
    row = {}
    for column in table_columns:
        row[column] = map_data[column]

    return row

def commit_all():
    """Commits any outstanding transactions into the database."""
    db.commit()


def insert_row(insert_obj):
    """Inserts a row into the database.

   `insert_obj` is a data structure which should contain all the metadata and
   data necessary for row insertion into the database.

    Args:
        insert_obj (InsertRowObject): A data structure containing all the
            metadata and data necessary for row insertion into the database.

    Raises:
        InvalidRowFormatError: Thrown if the row object is not a dict or is
            empty.  This is to maintain DB integrity.
    """
    if not isinstance(insert_obj.row, dict) or len(insert_obj.row) is 0:
        raise InvalidRowFormatError("Row type: {} is not a valid format for "
            "DB insertion.  Please make sure it is a `dict`.".format(
                type(insert_obj.row)))

    columns = *insert_obj.row,
    row_data = *insert_obj.row.values(),
    cursor = db.cursor()
    params = ', '.join(['%s'] * len(row_data))

    cursor.execute(
        _form_insert_query(
            insert_obj.table_name,
            columns,
            params,
            insert_obj.prim_key_columns),
        row_data)
    cursor.close()


def ping_db():
    """Ping the database to keep connection alive."""
    global db
    db.ping()


def start_db(db_user, db_password, db_name):
    """Starts the database by initiating a connection, if no connection exists.

    Args:
        db_user (str): The database user.
        db_password (str): The database password.
        db_name (str): The database name.
    """
    global db

    if db is None:
        db = MySQLdb.connect(user=db_user, passwd=db_password, db=db_name)
