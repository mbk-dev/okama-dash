import pytest

from common.math import round_list

pytestmark = pytest.mark.unit


class TestRoundList:
    def test_basic_rounding(self):
        result = round_list([1.234, 2.345, 3.456], 2)
        assert len(result) == 3
        assert all(isinstance(x, float) for x in result)

    def test_sum_preserved(self):
        original = [1.111, 2.222, 3.333, 4.444]
        result = round_list(original, 2)
        assert abs(sum(result) - sum(original)) < 0.01

    def test_sum_preserved_thirds(self):
        original = [100 / 3] * 3
        result = round_list(original, 2)
        assert abs(sum(result) - 100.0) < 0.01

    def test_empty_list(self):
        assert round_list([], 2) == []

    def test_single_element(self):
        result = round_list([3.14159], 2)
        assert result == [3.14]

    def test_negative_numbers(self):
        original = [-1.5, -2.5, -3.5]
        result = round_list(original, 0)
        assert abs(sum(result) - sum(original)) <= 0.5

    def test_all_zeros(self):
        assert round_list([0.0, 0.0, 0.0], 2) == [0.0, 0.0, 0.0]

    def test_zero_decimal_positions(self):
        result = round_list([1.5, 2.3, 3.7], 0)
        assert all(x == int(x) for x in result)
