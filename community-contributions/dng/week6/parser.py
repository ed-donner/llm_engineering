from contracts import ShippingContract


def parse_currency(text: str) -> int:
    return int(text.replace("$", "").replace(" USD", ""))


def get_quantity(text: str) -> int:
    return int(text.replace(" units", ""))


def get_total_weight(text: str) -> int:
    return int(text.replace(" kg", ""))


def get_value(text: str) -> int:
    return parse_currency(text)


def get_total_shipping_cost(text: str) -> int:
    return parse_currency(text)


def get_insurance_value(text: str) -> int:
    return parse_currency(text)


def get_penalty_for_late_delivery(text: str) -> int:
    text = text.replace(" per week of delay", "")
    return parse_currency(text)


def get_insurance_coverage(text: str) -> bool:
    return text.lower() == "yes"


def parse(datapoint: dict) -> ShippingContract:
    return ShippingContract(
        contract_number=datapoint["Contract Number"],
        effective_date=datapoint["Effective Date"],
        shipper=datapoint["Shipper"],
        receiver=datapoint["Receiver"],
        goods_description=datapoint["Goods Description"],
        quantity=get_quantity(datapoint["Quantity"]),
        total_weight=get_total_weight(datapoint["Total Weight"]),
        value=get_value(datapoint["Value"]),
        shipping_method=datapoint["Shipping Method"],
        origin=datapoint["Origin"],
        destination=datapoint["Destination"],
        estimated_delivery_date=datapoint["Estimated Delivery Date"],
        total_shipping_cost=get_total_shipping_cost(datapoint["Total Shipping Cost"]),
        payment_schedule=datapoint["Payment Schedule"],
        insurance_coverage=get_insurance_coverage(datapoint["Insurance Coverage"]),
        insurance_value=get_insurance_value(datapoint["Insurance Value"]),
        liability=datapoint["Liability"],
        penalty_for_late_delivery=get_penalty_for_late_delivery(
            datapoint["Penalty for Late Delivery"]
        ),
        grace_period=datapoint["Grace Period"],
        customs_and_compliance=datapoint["Customs and Compliance"],
        termination_notice=datapoint["Termination Notice"],
        jurisdiction=datapoint["Jurisdiction"],
        arbitration_location=datapoint["Arbitration Location"],
        keywords=datapoint["Keywords"],
        inventory_status=datapoint["Inventory Status"],
        current_transit_status=datapoint["Current Transit Status"],
    )
