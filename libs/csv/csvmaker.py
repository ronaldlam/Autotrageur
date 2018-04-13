import argparse
import csv
import os
import sys


def get_line_terminator():
    """Adds lineterminator param to the formatting options of csv writer.

    This gets around the Windows quirk where any '\n' is replaced with
    '\r\n'.  Thus, causing extra new lines in written csv files.
    The default lineterminator for a csv writer is '\r\n', thus becoming
    '\r\r\n' in Windows.

    Returns:
        str: '\n' for windows OS, otherwise '\r\n'
    """
    return '\n' if sys.platform.startswith('win') else '\r\n'


def dict_write_to_csv(col_headers, csv_filename, file_content):
    """Writes a CSV file with dict objects as rows.

    Args:
        col_headers (list(str)): The column header row for the csv file.
        csv_filename (str): The name of the csv file to be written.
        file_content (list(dict)): The rows of the file.  Each dict object is
            a row in the csv file.
    """
    with open(csv_filename, 'w') as csvfile:
        writer = csv.DictWriter(
            csvfile, col_headers, lineterminator=get_line_terminator())
        writer.writeheader()
        writer.writerows(file_content)
    print(
        csv_filename
        + " has finished being written.  Located at: "
        + os.getcwd())


def write_to_csv(csv_filename, file_content):
    """Writes a CSV file.

    Args:
        csv_filename (str): The name of the csv file to be written.
        file_content (list(list(str))): The rows of the file.  Be sure to
            include the column headers as the first row.
    """
    csv_file = open(csv_filename, 'w')
    with csv_file:
        writer = csv.writer(csv_filename, lineterminator=get_line_terminator())
        writer.writerows(file_content)
    print(
        csv_filename
        + " has finished being written.  Located at: "
        + os.getcwd())
