import re

import MySQLdb


# The database object.
db = None


class InvalidRowFormatError(Exception):
    """Thrown when a row object is deemed invalid for DB insertion (e.g. Wrong
    type, or empty)"""
    pass


def _form_insert_query(table_name, columns, param_string, prim_keys):
    """Forms an 'INSERT IGNORE INTO ...' query string.

    Utilizes regex to strip single quotes from the columns tuple string.

    Args:
        table_name (str): Name of the table to insert into.
        columns (tuple(str)): Column names represented as a tuple of strings.
        param_string (str): A param substitution string composed of repeating
            sequences of '%s'.  E.g. '%s, %s, %s"
        prim_keys (dict): Any primary keys of the supplied table,
            represented as a dict `{ COLUMN_NAME: PRIMARY_KEY_VALUE }`
    """
    # Form the initial 'INSERT INTO ...' query
    insert_query = (
        "INSERT INTO "
        + table_name
        + re.sub(r"((?<=\()('|\"))"              # single quote, look-behind '('
                 r"|(('|\")(?=,))"               # single quote, look-ahead ','
                 r"|((?<=[^\S\r\n\t]|,)('|\"))"  # single quote, look-behind space character, or ','
                 r"|(('|\")(?=\)))",             # single quote, look-ahead ')'
                 '', str(columns))
        + " VALUES ("
        + param_string
        + ")"
    )

    # Form redundant 'ON DUPLICATE KEY UPDATE ...' clause for 'ON CONFLICT DO
    # NOTHING' equivalent.
    redundant_update_prim_keys = ', '.join(
        "{} = \"{}\"".format(key,val) for (key,val) in prim_keys.items())

    if redundant_update_prim_keys:
        insert_query += (
            " ON DUPLICATE KEY UPDATE "
            + redundant_update_prim_keys
        )
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


def insert_row(table_name, row, prim_keys):
    """Inserts a row into the database.

    The row object is represented as a map with keys containing the columns,
    and values containing the corresponding row data.

    Args:
        table_name (str): The name of the table to insert into.
        row (dict): The row object containing the necessary information for
            insertion into database.
        prim_keys (dict): Any primary keys of the supplied table,
            represented as a dict `{ COLUMN_NAME: PRIMARY_KEY_VALUE }`

    Raises:
        InvalidRowFormatError: Thrown if the row object is not a dict or is
            empty.  This is to maintain DB integrity.
    """
    if not isinstance(row, dict) or len(row) is 0:
        raise InvalidRowFormatError("Row object: {} is not a valid format for "
            "DB insertion.  Please make sure it is a dict.".format(row))

    columns = *row,
    row_data = *row.values(),
    cursor = db.cursor()
    params = ', '.join(['%s'] * len(row_data))
    cursor.execute(
        _form_insert_query(table_name, columns, params, prim_keys),
        row_data)
    cursor.close()


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
