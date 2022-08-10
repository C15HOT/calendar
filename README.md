# core-calendar

Generated from cookiecutter template
---

## Development

### Install dependencies

```
pip install -r requirements-dev.txt -U
```

### Install git hooks

```
pre-commit install --install-hooks
```

## Run service

```
mv .env.example .env
python -m app
```

## Run pre-commit hooks

### Run whole hooks config

```
pre-commit run --all-files
```

### Run single hook

```
pre-commit run flake8 --all-files
```
