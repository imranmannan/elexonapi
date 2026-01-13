
# elexonapi ⚡️

A compact Python wrapper for the Elexon Insights API that
lets you download years of data at a time and 
use human-readable table names.  

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

# Browse all Elexon datasets interactively
elexon.browse()

# Pandas DataFrame of available datasets
print(elexon.datasets.head())

# Search for a dataset by alias and view help text
elexon.help('Initial Transmission System Demand outturn')  # name
# or
elexon.help('ITSDO')  # code
# or
elexon.help('get-datasets-itsdo')  # operation id
```

### Downloading a single request

```py
# Return a pandas DataFrame (format="df") when supported
elexon = elexonapi.ElexonClient()
df = elexon.download('ITSDO',publishDateTimeFrom='2025-01-06',publishDateTimeTo='2025-04-06')

# Or get raw JSON
df = elexon.download('ITSDO',publishDateTimeFrom='2025-01-06',publishDateTimeTo='2025-04-06', format='json')
```

### Downloading historical data (automatic chunking)

If an endpoint accepts a `from` and `to` range (or a single `date` / `time` column), `elexonapi.download` will automatically split the range into multiple queries and re-assemble the results for you.

```py
# Use `_from` to avoid the reserved Python word `from` in keywords
# The wrapper will chunk the range and return a single DataFrame
elexon = elexonapi.ElexonClient()
df = elexon.download('Minimum Zero Time', _from='2023-01-01', to='2023-01-30')

# Or iterate single dates
dates = pd.date_range('2024-01-01', '2024-02-01')
df = elexon.download('Total Exempt Supply Volume', settlementDate=dates)
```

### Examples showing alias flexibility

```py
# Query by human-friendly name
df = elexon.download('Initial Transmission System Demand outturn',publishDateTimeFrom='2025-01-06',publishDateTimeTo='2025-04-06')

# Query by code
df = elexon.download('ITSDO',publishDateTimeFrom='2025-01-06',publishDateTimeTo='2025-04-06')

# Query by operation id
df = elexon.download('get-datasets-itsdo',publishDateTimeFrom='2025-01-06',publishDateTimeTo='2025-04-06')
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
uv sync --dev

# Install the current project in editable mode
uv pip install -e .

# run tests
uv run pytest -q
```

> Note: The project is published on PyPI and the recommended install for users is via `pip install elexonapi`.

---

## Publishing to PyPI 

Follow the steps in `docs/RELEASING.md` to publish manually; the repository includes a GitHub Actions workflow (`.github/workflows/publish.yml`) that publishes on pushing a `vX.Y.Z` tag when the workflow has access to a `PYPI_API_TOKEN` secret.


## License

MIT — see `LICENSE` for details.
