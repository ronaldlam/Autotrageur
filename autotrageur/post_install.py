"""Post install script

Copies configuration and environment files to expected usage locations.
Before:
    - root
        - venv
            - autotrageur-data
                - .env.sample
                - basic_client.py
                - configs
                    ...
After:
    - root
        - .env.sample
        - basic_client.py
        - configs
            ...
        - venv
            ...

Usage:
    post_install [VENV]

Description:
    VENV            The venv/virtualenv name, defaults to venv
"""
from os import getcwd, listdir
from os.path import isdir, isfile, join, split
from shutil import copy2, copytree

from docopt import docopt

from autotrageur.version import VERSION


def _dir_list(in_dir):
    """Return a list of directories within the input parameter.

    Args:
        in_dir (str): The top level directory.

    Returns:
        list: The list of directories.
    """
    return [join(in_dir, d) for d in listdir(in_dir) if isdir(join(in_dir, d))]


def _file_list(in_dir):
    """Return a list of files within the input parameter.

    Args:
        in_dir (str): The top level directory.

    Returns:
        list: The list of files.
    """
    return [join(in_dir, f) for f in listdir(in_dir) if isfile(join(in_dir, f))]


def main():
    """The installed entry point."""
    arguments = docopt(__doc__, version=VERSION)

    venv = arguments['VENV'] or 'venv'
    cwd = getcwd()
    data_dir = join(cwd, venv, 'autotrageur-data')
    src_dirs = _dir_list(data_dir)
    src_files = _file_list(data_dir)

    for d in src_dirs:
        # This is the directory name.
        _, tail = split(d)
        # Copy contents of tree into directory of same name.
        copytree(d, join(cwd, tail))

    for f in src_files:
        copy2(f, cwd)


if __name__ == "__main__":
    main()
