def shipping_fee(
    order_total: int,
    is_member: bool,
    express: bool,
) -> int:
    if order_total < 0:
        raise ValueError("order_total cannot be negative")

    standard_fee = 0 if order_total >= 1000 or is_member else 80
    express_fee = 120 if express else 0

    return standard_fee + express_fee