import MySQLdb


# The database object.
db = None


class MariaDB:
    def __init__(self, db_user, db_password, db_name):
        # Connect the DB
        pass

    def get_cursor(self):
        pass

def start_db(db_user, db_password, db_name):
    global db

    if db is None:
        db = MariaDB(db_user, db_password, db_name)
        # db = MySQLdb.connect(user=db_user, passwd=db_password, db=db_name)

    cursor = db.get_cursor()


def persist(table_name, row):
    pass