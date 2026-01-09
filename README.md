
# elexonapi
=========
Lightweight Python client for the Elexon BMRS Insights API.

- Spec-driven (OpenAPI)
- Strict parameter validation
- Automatic looping for time windows and unit limits
- Retry & rate-limit handling

### to do:

- implement chunking by date for known max
    - allow user to set date_chunk cols if ambiguous

### maybe:
- add timezones to input (and output?)
- add chunking to lists based on user input
