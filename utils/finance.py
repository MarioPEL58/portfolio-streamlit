import numpy as np
def annual_to_daily_rate(r_annual: float, periods_per_year: int = 252) -> float:
    """
    Converte un tasso annuale in tasso giornaliero composto.

    r_annual: tasso annuale (es. 0.02 = 2%)
    returns: tasso giornaliero
    """

    if r_annual is None:
        return 0.0

    return (1 + r_annual) ** (1 / periods_per_year) - 1

def get_dynamic_max(base, value, benchmark=None):
    import numpy as np

    values = []

    for v in [base, value, benchmark]:
        if isinstance(v, (int, float)) and not np.isnan(v):
            values.append(v)

    if not values:
        return base

    return np.ceil(max(values) + 0.5)


