

def round_list(l: list, decimal_positions: int) -> list:
    """
    Round list values while maintaining the sum.
    """
    new_l = list()
    rest = 0.0
    for n in l:
        new_n = round(n + rest,decimal_positions)
        rest += n - new_n
        new_l.append(new_n)
    return new_l