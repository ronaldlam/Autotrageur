# Autotrageur
The automated arbitrageur
## Versioning
We use [setuptools-scm](https://github.com/pypa/setuptools_scm) to automate versioning in code. Once a git tag is made, use this to retrieve the current version:
```python
from setuptools_scm import get_version
version = get_version()
```
By default, the working version if changes are made automatically increment the last numeric component of the tag. See [here](https://github.com/pypa/setuptools_scm#default-versioning-scheme) for details. If the current changes do not warrant a change in at least the hotfix number, this can be used to keep the existing last tag as the version prefix:
```python
version = get_version(version_scheme='post-release')
```
Using this means that version tagging needs to be part of the development branch history, and merging back into staging before branching into development branches will be necessary.

## Updating dependencies
### Third party dependencies
We have at least one nested dependency that is platform specific. Instead of `pip freeze` to list dependencies, use `pipdeptree -f | grep -P '^[\w0-9\-=.]+'` to get only top level dependencies. To save:
```
pipdeptree -f | grep -P '^[\w0-9\-=.]+' > requirements.txt
```
See [pipdeptree docs](https://github.com/naiquevin/pipdeptree#using-pipdeptree-to-write-requirementstxt-file) for more details.
#### OSX instructions
By default, BSD `grep` does not have the `-P` flag. See [here](https://stackoverflow.com/questions/16658333/grep-p-no-longer-works-how-can-i-rewrite-my-searches) and use this instead:
```
pipdeptree -f | perl -nle 'print if m{^[\w0-9\-=.]+}' > requirements.txt
```
### First party dependencies
In order to install directly from `pip`, the desired package must either be available through the default package index or specified directly. We access our internal libraries through the `requirements.txt` file by replacing `firstpartylibs-<version>` with:
```
git+ssh://git@github.com/ronaldlam/FirstPartyLibs.git@<version>#egg=firstpartylibs
```
See the internal [FirstPartyLibs](https://github.com/ronaldlam/FirstPartyLibs) repository for more details.

## Run Bandit
Security focused static code analysis tool. Optionally run with `-v` for list of files checked.
```
pip install bandit
bandit -r bot libs analytics *.py
```

## Run safety
Checks dependencies against database of known vulnerabilities. Updated monthly, so run every month or whenever dependencies are updated.
```
pip install safety
safety check -r requirements.txt
```

## Run Autotrageur
The following are examples of commands that would work. Top level scripts listed below are documented using `docopt`, so using a `-h` command will bring up usage instructions.
### Script list
- `archive_logs.py`
- `basic_client.py`
- `encrypt_file.py`
- `run_autotrageur.py`
- `scrape_forex.py`
- `spawn_ohlcv_minute.py`
### Installation
Use python 3.6, that's what we use.
#### Development or running from source
```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```
#### Through pip
```
pip install git+ssh://git@github.com/ronaldlam/Autotrageur.git[@<version/branch>]
```
### Setup configuration
Environment variables:
- rename `.env.sample` to `.env` and include any necessary environment variables.
Modify:
- `configs/arb_config.yaml`
- `configs/email_info.yaml`
### Encrypt your keys
```
python encrypt_file.py secret.txt
```
### Run!
The workhorse:
```
python run_autotrageur.py configs/arb_config.yaml encrypted-secret.txt
```
In a separate process, run to archive logs daily.
```
python archive_logs.py
```
