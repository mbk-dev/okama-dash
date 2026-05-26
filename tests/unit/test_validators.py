import pytest

from common.validators import validate_integer, validate_integer_bool

pytestmark = pytest.mark.unit


class TestValidateInteger:
    def test_valid_integer_passes(self):
        validate_integer("x", 5)

    def test_rejects_float(self):
        with pytest.raises(TypeError, match="must be an integer"):
            validate_integer("x", 3.14)

    def test_rejects_string(self):
        with pytest.raises(TypeError, match="must be an integer"):
            validate_integer("x", "hello")

    def test_rejects_none(self):
        with pytest.raises(TypeError, match="must be an integer"):
            validate_integer("x", None)

    def test_min_exclusive_rejects_equal(self):
        validate_integer("x", 6, min_value=5)
        with pytest.raises(ValueError, match="must be >= 5"):
            validate_integer("x", 5, min_value=5)

    def test_min_exclusive_rejects_below(self):
        with pytest.raises(ValueError, match="must be >= 5"):
            validate_integer("x", 4, min_value=5)

    def test_min_inclusive_allows_equal(self):
        validate_integer("x", 5, min_value=5, inclusive=True)

    def test_min_inclusive_rejects_below(self):
        with pytest.raises(ValueError, match="must be > 5"):
            validate_integer("x", 4, min_value=5, inclusive=True)

    def test_max_exclusive_rejects_equal(self):
        validate_integer("x", 4, max_value=5)
        with pytest.raises(ValueError, match="must be <= 5"):
            validate_integer("x", 5, max_value=5)

    def test_max_exclusive_rejects_above(self):
        with pytest.raises(ValueError, match="must be <= 5"):
            validate_integer("x", 6, max_value=5)

    def test_max_inclusive_allows_equal(self):
        validate_integer("x", 5, max_value=5, inclusive=True)

    def test_max_inclusive_rejects_above(self):
        with pytest.raises(ValueError, match="must be < 5"):
            validate_integer("x", 6, max_value=5, inclusive=True)

    def test_custom_min_message(self):
        with pytest.raises(ValueError, match="too small"):
            validate_integer("x", 0, min_value=5, custom_min_message="too small")

    def test_custom_max_message(self):
        with pytest.raises(ValueError, match="too big"):
            validate_integer("x", 100, max_value=5, custom_max_message="too big")

    def test_both_bounds_inclusive(self):
        validate_integer("x", 5, min_value=1, max_value=10, inclusive=True)
        with pytest.raises(ValueError):
            validate_integer("x", 0, min_value=1, max_value=10, inclusive=True)
        with pytest.raises(ValueError):
            validate_integer("x", 11, min_value=1, max_value=10, inclusive=True)


class TestValidateIntegerBool:
    def test_valid_positive_integer_returns_false(self):
        assert validate_integer_bool(5) is False

    def test_one_returns_false(self):
        assert validate_integer_bool(1) is False

    def test_zero_returns_true(self):
        assert validate_integer_bool(0) is True

    def test_negative_returns_true(self):
        assert validate_integer_bool(-1) is True

    def test_none_returns_true(self):
        assert validate_integer_bool(None) is True

    def test_string_returns_true(self):
        assert validate_integer_bool("abc") is True
