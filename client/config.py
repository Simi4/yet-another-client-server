import json
from dataclasses import dataclass
from pathlib import Path


cfg_path = Path('data/client_config.json')


@dataclass(init=False)
class AppConfig:
    host: str
    port: int

    def __init__(self):
        try:
            # attempt to read config from a file
            with cfg_path.open('r') as f:
                data = json.load(f)
            self.host = data['host']
            self.port = int(data['port'])
        except:
            # default config
            self.host = 'localhost'
            self.port = 1234
