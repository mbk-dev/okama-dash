"""Shared pure helpers for the Cash Flow card."""


def _prefill_amount(value, fallback):
    """Coerce a URL-prefill string to a number for dmc.NumberInput.

    Query params arrive as strings; NumberInput needs a real number to apply
    the thousands separator. Unset (falsy) or unparseable input falls back."""
    if not value:
        return fallback
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    return int(number) if number.is_integer() else number
