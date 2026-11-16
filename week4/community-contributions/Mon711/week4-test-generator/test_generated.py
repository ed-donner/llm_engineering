import pytest

from solution import shipping_fee


@pytest.mark.parametrize(
    ("order_total", "is_member", "express", "expected"),
    [
        (0, False, False, 80),
        (0, False, True, 200),
        (0, True, False, 0),
        (0, True, True, 120),
        (999, False, False, 80),
        (999, False, True, 200),
        (999, True, False, 0),
        (999, True, True, 120),
        (1000, False, False, 0),
        (1000, False, True, 120),
        (1000, True, False, 0),
        (1000, True, True, 120),
        (1001, False, False, 0),
        (1001, False, True, 120),
    ],
)
def test_shipping_fee(order_total, is_member, express, expected):
    result = shipping_fee(order_total, is_member, express)

    assert result == expected
    assert isinstance(result, int)


@pytest.mark.parametrize(
    ("is_member", "express"),
    [
        (False, False),
        (False, True),
        (True, False),
        (True, True),
    ],
)
def test_negative_order_total_raises_value_error(is_member, express):
    with pytest.raises(ValueError):
        shipping_fee(-1, is_member, express)


@pytest.mark.parametrize("order_total", [-1, -1000])
def test_all_negative_totals_raise_value_error(order_total):
    with pytest.raises(ValueError):
        shipping_fee(order_total, False, False)