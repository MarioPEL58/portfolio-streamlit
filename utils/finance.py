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
    values = [base, value]

    if benchmark is not None and not np.isnan(benchmark):
        values.append(benchmark)

    return np.ceil(max(values) + 0.5)
