# envdiff

`envdiff` compares two `.env` files and reports keys that are missing, extra, or changed.

## Usage

```sh
python envdiff.py old.env new.env
python envdiff.py old.env new.env --json
python envdiff.py old.env new.env --ignore DEBUG,LOG_LEVEL
```

By default, values are not printed. Use `--show-values` to include them.

## Tests

```sh
python -m pytest
```
