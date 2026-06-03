from datetime import date
from enum import Enum
from typing import Optional, Self

from datasets import Dataset, DatasetDict, load_dataset
from pydantic import BaseModel, computed_field


class Status(str, Enum):
    DELAYED = "Delayed"
    ON_SCHEDULE = "On Schedule"


class ShippingMethod(str, Enum):
    AIR_FREIGHT = "Air Freight"
    OCEAN_FREIGHT = "Ocean Freight"
    RAIL_FREIGHT = "Rail Freight"
    ROAD_FREIGHT = "Road Freight"


class Origin(str, Enum):
    DUBAI = "Port of Dubai, UAE"
    LOS_ANGELES = "Port of Los Angeles, USA"
    MELBOURNE = "Port of Melbourne, Australia"
    MIAMI = "Port of Miami, USA"
    NEW_YORK = "Port of New York, USA"
    ROTTERDAM = "Port of Rotterdam, Netherlands"
    SANTOS = "Port of Santos, Brazil"
    TOKYO = "Port of Tokyo, Japan"
    SHANGHAI = "Shanghai Port, China"


class Destination(str, Enum):
    ANTWERP = "Port of Antwerp, Belgium"
    CAPE_TOWN = "Port of Cape Town, South Africa"
    DUBAI = "Port of Dubai, UAE"
    GENOA = "Port of Genoa, Italy"
    HAMBURG = "Port of Hamburg, Germany"
    LAGOS = "Port of Lagos, Nigeria"
    LE_HAVRE = "Port of Le Havre, France"
    MARSEILLE = "Port of Marseille, France"
    MELBOURNE = "Port of Melbourne, Australia"
    MUMBAI = "Port of Mumbai, India"
    PIRAEUS = "Port of Piraeus, Greece"
    ROTTERDAM = "Port of Rotterdam, Netherlands"
    SANTOS = "Port of Santos, Brazil"
    SINGAPORE = "Port of Singapore, Singapore"
    SOUTHAMPTON = "Port of Southampton, UK"
    TOKYO = "Port of Tokyo, Japan"
    VALENCIA = "Port of Valencia, Spain"
    VANCOUVER = "Port of Vancouver, Canada"


class PaymentSchedule(str, Enum):
    TWENTY_PERCENT_UPFRONT = "20% upfront, 80% on delivery"
    THIRTY_PERCENT_UPFRONT = "30% upfront, 70% on delivery"
    FIFTY_PERCENT_UPFRONT = "50% upfront, 50% on delivery"
    SIXTY_PERCENT_UPFRONT = "60% upfront, 40% after 30 days of delivery"
    FULL_PAYMENT_ON_DELIVERY = "Full payment on delivery"


class Liability(str, Enum):
    DAMAGE_LIABILITY_ONLY = "Damage liability only, no theft coverage"
    FULL_LIABILITY_UP_TO_MAXIMUM_CONTRACT_VALUE = (
        "Full liability up to maximum contract value"
    )
    LOSS_DURING_TRANSIT_ONLY = "Loss during transit only"
    LOSS_OR_DAMAGE_UP_TO_INSURED_VALUE = "Loss or damage up to insured value"
    LOSS_DAMAGE_OR_THEFT_UP_TO_INSURED_VALUE = (
        "Loss, damage, or theft up to insured value"
    )


class Customs(str, Enum):
    RECEIVER = "Handled by receiver"
    SHIPPER = "Handled by shipper"
    JOINT_RESPONSIBILITY = "Joint responsibility"
    SHIPPER_RESPONSIBLE_FOR_US_CUSTOMS = (
        "Shipper responsible for US customs; receiver for destination customs"
    )
    THIRD_PARTY = "Third-party customs broker required"


class TerminationNotice(str, Enum):
    FIFTEEN_DAYS_WITH_MUTUAL_CONSENT = "15 days with mutual consent"
    THIRTY_DAYS = "30 days"
    FORTY_FIVE_DAYS = "45 days"
    SIXTY_DAYS = "60 days"
    NINETY_DAYS_FOR_STRATEGIC_CONTRACTS = "90 days for strategic contracts"
    IMMEDIATE_FOR_BREACH = "Immediate for breach"


class GracePeriod(str, Enum):
    SEVEN_DAYS = "7 days"
    FIFTEEN_DAYS = "15 days"
    THIRTY_DAYS = "30 days"
    FORTY_FIVE_DAYS = "45 days"
    SIXTY_DAYS = "60 days"
    NINETY_DAYS = "90 days"


class Jurisdiction(str, Enum):
    AUSTRALIA = "Australia"
    BRAZIL = "Brazil"
    CHINA = "China"
    GERMANY = "Germany"
    INDIA = "India"
    JAPAN = "Japan"
    UAE = "UAE"
    UNITED_KINGDOM = "United Kingdom"
    UNITED_STATES = "United States"


class ArbitrationLocation(str, Enum):
    BERLIN = "Berlin, Germany"
    DUBAI = "Dubai, UAE"
    LONDON = "London, UK"
    MUMBAI = "Mumbai, India"
    NEW_YORK = "New York, NY"
    SAO_PAULO = "Sao Paulo, Brazil"
    SHANGHAI = "Shanghai, China"
    SYDNEY = "Sydney, Australia"
    TOKYO = "Tokyo, Japan"


class Keywords(str, Enum):
    AUTOMOTIVE_PARTS = "automotive parts"
    BULK_ORDER = "bulk order"
    CLIMATE_SENSITIVE_ITEMS = "climate-sensitive items"
    DELICATE_MACHINERY = "delicate machinery"
    FRAGILE_GOODS = "fragile goods"
    HIGH_SECURITY_REQUIRED = "high security required"
    HIGH_VALUE_ELECTRONICS = "high value electronics"
    LONG_DISTANCE_TRANSPORT = "long-distance transport"
    LUXURY_GOODS = "luxury goods"
    MEDICAL_EQUIPMENT = "medical equipment"
    NON_HAZARDOUS_MATERIAL = "non-hazardous material"
    PERISHABLE_GOODS = "perishable goods"
    TEXTILES_AND_FABRICS = "textiles and fabrics"
    TIME_SENSITIVE = "time-sensitive delivery"
    URGENT_SHIPMENT = "urgent shipment"


class InventoryStatus(str, Enum):
    AWAITING_CUSTOMS_CLEARANCE = "Awaiting Customs Clearance"
    DELIVERED = "Delivered"
    IN_TRANSIT = "In Transit"
    PENDING = "Pending Dispatch"


PREFIX = "Total shipping cost is $"
QUESTION = "What is the total shipping cost?"


class Description(str, Enum):
    AUTOMOTIVE_PARTS = "Automotive Parts"
    CLOTHING = "Clothing"
    COSMETICS = "Cosmetics"
    ELECTRONICS = "Electronics"
    FOOD_ITEMS = "Food Items"
    FURNITURE = "Furniture"
    MACHINERY = "Machinery"
    PHARMACEUTICALS = "Pharmaceuticals"
    TEXTILES = "Textiles"
    TOYS = "Toys"


class ShippingContract(BaseModel):
    """
    A Shipping Contract is a data-point of a contract between a shipper and a receiver for the transportation of goods.
    """

    contract_number: str
    effective_date: date
    shipper: str
    receiver: str
    goods_description: Description
    quantity: int
    total_weight: int
    value: int
    shipping_method: ShippingMethod
    origin: Origin
    destination: Destination
    estimated_delivery_date: date
    total_shipping_cost: int
    payment_schedule: PaymentSchedule
    insurance_coverage: bool
    insurance_value: int
    liability: Liability
    penalty_for_late_delivery: int
    grace_period: GracePeriod
    customs_and_compliance: Customs
    termination_notice: TerminationNotice
    jurisdiction: Jurisdiction
    arbitration_location: ArbitrationLocation
    keywords: Keywords
    inventory_status: InventoryStatus
    current_transit_status: Status
    prompt: Optional[str] = None
    summary: Optional[str] = None

    @computed_field
    @property
    def full(self) -> str:
        return f"""
        Shipment {self.contract_number} effective {self.effective_date}
        Shipper: {self.shipper}
        Receiver: {self.receiver}
        Goods: {self.quantity} units of {self.goods_description.value} weighing {self.total_weight} kg, and worth ${self.value:,} USD
        Shipping Method: {self.shipping_method.value}
        Origin: {self.origin.value}
        Destination: {self.destination.value}
        Estimated Delivery Date: {self.estimated_delivery_date.strftime("%Y-%m-%d")}
        Total Shipping Cost: ${self.total_shipping_cost:,} USD
        Payment Schedule: {self.payment_schedule.value}
        Insurance Coverage: {self.insurance_coverage}
        Insurance Value: ${self.insurance_value:,} USD
        Liability: {self.liability.value}
        Penalty for Late Delivery: ${self.penalty_for_late_delivery:,} USD per week of delay
        Grace Period: {self.grace_period.value}
        Customs and Compliance: {self.customs_and_compliance.value}
        Termination Notice: {self.termination_notice.value}
        Jurisdiction: {self.jurisdiction.value}
        Arbitration Location: {self.arbitration_location.value}
        Keywords: {self.keywords.value}
        Inventory Status: {self.inventory_status.value}
        Current Transit Status: {self.current_transit_status.value}"""

    def make_prompt(self, text: str):
        self.prompt = f"{QUESTION}\n\n{text}\n\n{PREFIX}{self.total_shipping_cost}"

    def test_prompt(self) -> Optional[str]:
        return self.prompt.split(PREFIX)[0] + PREFIX if self.prompt else None

    def __repr__(self) -> str:
        return f"<Contract {self.contract_number} = ${self.total_shipping_cost}>"

    @staticmethod
    def push_to_hub(
        dataset_name: str, train: list[Self], val: list[Self], test: list[Self]
    ):
        """Push ShippingContract lists to HuggingFace Hub"""
        DatasetDict(
            {
                "train": Dataset.from_list([item.model_dump() for item in train]),
                "validation": Dataset.from_list([item.model_dump() for item in val]),
                "test": Dataset.from_list([item.model_dump() for item in test]),
            }
        ).push_to_hub(dataset_name)

    @classmethod
    def from_hub(cls, dataset_name: str) -> tuple[list[Self], list[Self], list[Self]]:
        """Load from HuggingFace Hub and reconstruct ShippingContracts"""
        ds: Dataset = load_dataset(dataset_name)
        return (
            [cls.model_validate(row) for row in ds["train"]],
            [cls.model_validate(row) for row in ds["validation"]],
            [cls.model_validate(row) for row in ds["test"]],
        )
