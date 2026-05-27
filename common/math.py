def round_list(values: list, decimal_positions: int) -> list:
    """
    Round list values while maintaining the sum.
    """
    result = []
    rest = 0.0
    for n in values:
        new_n = round(n + rest, decimal_positions)
        rest += n - new_n
        result.append(new_n)
    return result
