import re

import MySQLdb


# The database object.
db = None

def _form_insert_ignore_query(table_name, columns, param_string):
    """Forms an 'INSERT IGNORE INTO ...' query string.

    Utilizes regex to strip single quotes from the columns tuple string.

    Args:
        table_name (str): Name of the table to insert into.
        columns (tuple(str)): Column names represented as a tuple of strings.
        param_string (str): A param substitution string composed of repeating
            sequences of '%s'.  E.g. '%s, %s, %s"
    """

    return (
        "INSERT IGNORE INTO "
        + table_name
        + re.sub(r"((?<=\()')"              # single quote, look-behind '('
                r"|('(?=,))"               # single quote, look-ahead ','
                r"|((?<=[^\S\r\n\t]|,)')"  # single quote, look-behind space character, or ','
                r"|('(?=\)))",             # single quote, look-ahead ')'
                '', str(columns))
        + " VALUES (" + param_string + ")"
    )


def build_row(table_columns, map_data):
    """Builds a row designated for the table columns provided.

    Extracts the necessary keys from `map_data` and returns a newly formed map
    which represents the row data to be inserted into the table.

    Args:
        table_columns (list): A list of column names for the row to be built
            against.
        map_data (dict): A map containing more entries than a row designated
            against `table_columns`.

    Returns:
        dict: A row object represented as a map with the filtered entries for
            `table_columns`.
    """
    row = {}
    for column in table_columns:
        row[column] = map_data[column]

    return row

def commit_all():
    """Commits any outstanding transacations into the databse."""
    db.commit()


def insert_row(table_name, row):
    """Inserts a row into the database.

    The row object is represented as a map with keys containing the columns,
    and values containing the corresponding row data.

    Args:
        table_name (str): The name of the table to insert into.
        row (dict): The row object containing the necessary information for
            insertion into database.
    """
    columns = *row,
    row_data = *row.values(),
    cursor = db.cursor()
    params = ''
    for i in range(len(row_data)):
        params += '%s, '
    cursor.execute(
        _form_insert_ignore_query(table_name, columns, params[:-2]),
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
