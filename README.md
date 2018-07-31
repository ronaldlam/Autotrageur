# Autotrageur
The automated arbitrageur

## Testing
Start at the top level directory of the project (Autotrageur).
### To run all tests:
```
python -m pytest
```
### To run a particular file, add the file:
```
python -m pytest tests/unit/libs/test_utilities.py
```
### To run a particular test of the file:
```
python -m pytest tests/unit/libs/test_utilities.py::test_not_keys_exists
```

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