import time
import modal
from datetime import datetime

Pricer = modal.Cls.lookup("pricer-service", "Pricer")
pricer = Pricer()
while True:
    reply = pricer.wake_up.remote()
    print(f"{datetime.now()}: {reply}")
    time.sleep(30)