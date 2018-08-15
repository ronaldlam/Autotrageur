# Autotrageur
The automated arbitrageur
## Updating dependencies
### Third party dependencies
We have at least one nested dependency that is platform specific. Instead of `pip freeze` to list dependencies, use `pipdeptree -f | grep -P '^[\w0-9\-=.]+'` to get only top level dependencies. To save:
```
pipdeptree -f | grep -P '^[\w0-9\-=.]+' > requirements.txt
```
See [pipdeptree docs](https://github.com/naiquevin/pipdeptree#using-pipdeptree-to-write-requirementstxt-file) for more details.
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
- `encrypt_file.py`
- `run_autotrageur.py`
- `spawn_ohlcv_minute.py`
### Install requirements
```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
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