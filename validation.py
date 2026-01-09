
def validate_params(dataset, params):
    allowed = set(dataset["required_cols"] + dataset["optional_cols"])
    missing = set(dataset["required_cols"]) - set(params)
    extra = set(params) - allowed

    if missing:
        raise ValueError(f"Missing required parameters: {missing}")
    if extra:
        raise ValueError(f"Unknown parameters: {extra}")
