from dataclasses import dataclass
from datetime import datetime


@dataclass(init=False)
class Session:
    time: datetime

    def __init__(self):
        self.time = datetime.utcnow()
