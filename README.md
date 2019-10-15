# poc-cloud-storage

[poc-cloud-storage](https://github.com/michaelheyman/poc-cloud-storage/) is part of the
[pdx-schedule](https://github.com/michaelheyman/pdx-schedule/) project.

Runs a Cloud Function that retrieves the latest unprocessed structured JSON data
from a bucket that has the output of running
[poc-google-function](https://github.com/michaelheyman/poc-google-function/).

The purpose of this Cloud Function is then to extract the instructor information
from the unprocessed structured JSON, retreive instructor metadata, and inject
back the instructor information with that metadata.

## Setup

### Create Virtual Environment

```bash
pyenv virtualenv 3.7.3 poc-cloud-storage-3.7.3
pyenv activate poc-cloud-storage-3.7.3
```

### Install Requirements

```bash
pip -r install requirements.txt
```

### Install Git Hooks

See [.pre-commit-config.yaml](.pre-commit-config.yaml) for information on which hooks are configured.

```bash
pre-commit install
```

```bash
pre-commit install -t pre-push
```

## Running

Run the application by executing

```bash
python -m app
```

## Testing

Ensure that `pytest` and `pytest-cov` are installed:

```bash
pip install pytest pytest-cov
```

Run `pytest` with verbose output:

```bash
pytest -vv
```

Run `pytest` with coverage:

```bash
pytest --cov=app tests/
```

```bash
pytest --cov-report html --cov=app tests/
```
