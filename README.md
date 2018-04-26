# Autotrageur
The automated arbitrageur

## Testing
Start at the top level directory of the project (Autotrageur). To run all tests:
```python -m pytest```
To run a particular file, add the file:
```python -m pytest tests/unit/libs/test_utilities.py```
To run a particualr test of the file:
```python -m pytest tests/unit/libs/test_utilities.py::test_not_keys_exists```
