
# elexonapi ⚡️

A compact, well-documented Python wrapper for the Elexon Insights API that
makes downloading and working with Elexon datasets easy and legible.

Key differentiators:
- **Insights API (not BMRS)** — This package targets the newer Elexon *Insights* OpenAPI spec and endpoints.
- **Automatic historical downloads** — Request a date range and the library will loop and chunk queries for you in the background so you can fetch long histories without manual slicing.
- **Flexible aliasing** — Query datasets by **operation id**, **code**, or **human-friendly name** (choose the style that makes your code most readable).
- **Clear error messages** — When parameters are missing, or a dataset doesn't support `format="df"`, errors explain which parameters are required and which formats are allowed.

---

## Quick install

Install the latest release from PyPI:

```bash
pip install elexonapi
```

If you need the development version and want to run the package locally, see the **Local development** section below (we recommend using `uv` to manage and sync project dependencies locally).

---

## Basic usage ⚙️

Import the small API and inspect what datasets are available:

```py
from elexonapi import ElexonClient

elexon = ElexonClient()

# Pandas DataFrame of available datasets
print(elexon.datasets.head())

# Search for a dataset by alias and view help text
elexon.help('BMU - Balancing Mechanism Unit Details')  # name
# or
elexon.help('BMUDETAILS')  # code
# or
elexon.help('bmuDetailsSeeAll')  # operation id
```

### Downloading a single request

```py
# Return a pandas DataFrame (format="df") when supported
elexon = elexonapi.ElexonClient()
df = elexon.download('BMUDETAILS', market='BM')

# Or get raw JSON
j = elexon.download('BMUDETAILS', format='json', market='BM')
```

### Downloading historical data (automatic chunking)

If an endpoint accepts a `from` and `to` range (or a single `date` / `time` column), `elexonapi.download` will automatically split the range into multiple queries and re-assemble the results for you.

```py
# Use `_from` to avoid the reserved Python word `from` in keywords
# The wrapper will chunk the range and return a single DataFrame
elexon = elexonapi.ElexonClient()
df = elexon.download('BMUDETAILS', _from='2023-01-01', to='2023-06-30')

# Or iterate single dates
dates = pd.date_range('2024-01-01', '2024-01-07')
weekly = elexonapi.download('SOME_DAILY_ENDPOINT', date=dates)
```

### Examples showing alias flexibility

```py
# Query by human-friendly name
elexonapi.download('Balancing Mechanism Unit Details', _from='2024-01-01', to='2024-01-10')

# Query by code
elexonapi.download('BMUDETAILS', _from='2024-01-01', to='2024-01-10')

# Query by operation id
elexonapi.download('bmuDetailsSeeAll', _from='2024-01-01', to='2024-01-10')
```

### Helpful error messages

- If you forget required parameters the library raises an error like:

```
ValueError: Missing required parameters: ['from', 'to']
```

- If you request `format="df"` for an endpoint that only supports JSON, you'll see:

```
ValueError: This dataset does not support format="df". Use format="json" to retrieve the raw data.
```

---

## Plaintext diagram of code flow

```
User code
   |
   |  (provide alias + params)
   v
get_operation_from_alias(alias)  <-- looks up operation id from (operation, name, code)
   |
   v
resolve dataset metadata (path, required/optional params, datetime cols)
   |
validate_params(dataset, params)  <-- helpful errors on missing/extra params
   |
if no date columns: request_with_retry -> return_response
else if date range: datetime_chunks -> multiple requests -> concat results
else if date list: iterate list -> multiple requests -> concat results
   |
return pandas.DataFrame (format="df") or JSON (format="json")
```

---

## Contributing

- Please open an issue or PR for inconsistencies or improvements.
- The package is fully typed and documented to make maintenance easier.
---

## Local development (using `uv`) 🧰

If you want to run the project locally (tests, linting, or editable installs) use `uv` to add dev dependencies and sync the project into an active environment.

```bash
# add development tooling
uv add --dev pytest mypy flake8

# sync/install into the active virtual environment
uv sync --active

# If you prefer pip to install the current project in editable mode
# (useful if you have an editable layout), run:
uv pip install -e .

# run tests
pytest -q
```

> Note: The project is published on PyPI and the recommended install for users is via `pip install elexonapi`.

---

## Publishing to PyPI 

Follow the steps in `docs/RELEASING.md` to publish manually; the repository includes a GitHub Actions workflow (`.github/workflows/publish.yml`) that publishes on pushing a `vX.Y.Z` tag when the workflow has access to a `PYPI_API_TOKEN` secret.


## License

MIT — see `LICENSE` for details.
