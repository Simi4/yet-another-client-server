import json
from dataclasses import dataclass, asdict
from pathlib import Path


cfg_path = Path('data/server_config.json')


@dataclass(init=False)
class ServerConfig:
    credits_range_begin: int
    credits_range_end: int
    host: str
    port: int

    def __init__(self):
        try:
            # attempt to read config from a file
            self.read_config()

        except Exception:
            # use default config
            self.init_defaults()

            try:
                # attempt to write default config
                self.write_config()

            except Exception:
                # do nothing
                pass

    def init_defaults(self):
        self.credits_range_begin = 50_000
        self.credits_range_end = 100_000
        self.host = 'localhost'
        self.port = 1234

    def read_config(self):
        with cfg_path.open('r') as f:
            data = json.load(f)
        self.credits_range_begin = int(data['credits_range_begin'])
        self.credits_range_end = int(data['credits_range_end'])
        self.host = data['host']
        self.port = int(data['port'])

    def write_config(self):
        with cfg_path.open('w') as f:
            json.dump(asdict(self), f, indent=4)
