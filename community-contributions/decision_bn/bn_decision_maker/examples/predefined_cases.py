"""
Predefined example cases for decision analysis.
"""

CASE_VEHICLE_OVERHEAT = """
In a car, the coolant level can be either Low (0.15) or Normal (0.85). The radiator fan works correctly with probability 0.95, but if the coolant is low, it tends to fail more often: 0.85 working, 0.15 failed. The engine temperature depends on both variables. When the coolant is normal and the fan works, the engine overheats only 2% of the time. If either the coolant is low or the fan fails, overheating rises to 40%, and if both fail, overheating occurs 90% of the time.
The driver must decide whether to continue driving or stop immediately. If the engine is actually overheating, continuing gives a utility of –200 (engine damage), and stopping gives +50 (safe outcome). If the engine is normal, continuing gives +100, while stopping unnecessarily gives +70.
"""

CASE_MANUFACTURING_LINE_JAM = """
In a packaging line, the conveyor motor condition is Good (0.9) or Worn (0.1). The sensor alignment is Proper (0.8) or Misaligned (0.2). A line jam depends on both — if both are good, the jam probability is 2%, but if either is bad it rises to 25%, and if both are faulty it jumps to 70%.
When the jam occurs, a warning light turns on with 95% accuracy; when no jam exists, it falsely turns on 5% of the time. The operator can decide to pause production for inspection or continue running. If the line is jammed and the operator continues, the utility is –100 (damage), while pausing yields +30 (minor downtime). If there's no jam, continuing yields +80, and pausing unnecessarily yields +50.
"""

CASE_HOME_HEATING = """
A home's window insulation is Good (0.85) or Poor (0.15). The heater thermostat can be Calibrated (0.9) or Faulty (0.1). The energy consumption depends on both: if insulation and thermostat are good, high energy use occurs only 10% of the time; if either is bad, it rises to 40%, and if both are bad, 80%.
The homeowner decides whether to call maintenance or ignore. If the system is inefficient (high energy use), calling gives +40 (saves future cost) and ignoring gives –60 (wasted bills). If efficiency is normal, calling unnecessarily costs –10, while ignoring gives +20.
"""

CASE_FRAUD_DETECTION = """
When the card holder is travelling abroad, fraudulent transactions are more likely since tourists are prime targets
for thieves. More precisely, 1% of transactions are fraudulent when the card holder is travelling, where as only
0.4% of the transactions are fraudulent when they are not travelling. On average, 5% of all transactions happen
while the card holder is travelling. If a transaction is fraudulent, then the likelihood of a foreign purchase
increases, unless the card holder happens to be travelling. More precisely, when the card holder is not travelling,
10% of the fraudulent transactions are foreign purchases where as only 1% of the legitimate transactions are
foreign purchases. On the other hand, when the card holder is travelling, then 90% of the transactions are
foreign purchases regardless of the legitimacy of the transactions.
• Purchases made over the internet are more likely to be fraudulent. This is especially true for card holders who
don’t own any computer. Currently, 60% of the population owns a computer and for those card holders, 1% of
their legitimate transactions are done over the internet, however this percentage increases to 2% for fraudulent
transactions. For those who don’t own any computer, a mere 0.1% of their legitimate transactions is done
over the internet, but that number increases to 1.1% for fraudulent transactions. Unfortunately, the credit card
company doesn’t know whether a card holder owns a computer, however if someone owns a computers, they are very likely
to purchase a computer-related accessory. In any given week, 10% of those who own a computer purchase with their
credit card at least one computer related accessory item as opposed to just 0.1% of those who don’t own any computer.
Therefore, a computer related accessory purchase is a strong indicator that the card holder owns a computer.
"""

# Mapping for easy access
PREDEFINED_CASES = {
    "Vehicle Overheat": CASE_VEHICLE_OVERHEAT,
    "Manufacturing Line Jam": CASE_MANUFACTURING_LINE_JAM,
    "Home Heating Efficiency": CASE_HOME_HEATING,
    "Credit Card Fraud Detection": CASE_FRAUD_DETECTION
}
