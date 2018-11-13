from pkg_resources import get_distribution, DistributionNotFound
from setuptools_scm import get_version

try:
    # We try to get the installed version by default.
    VERSION = get_distribution('autotrageur').version
except DistributionNotFound:
    # Otherwise grab the local version.
    VERSION = get_version()
