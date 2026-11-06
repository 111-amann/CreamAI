
from dataclasses import dataclass, asdict


@dataclass
class Record:
    id: int
    module: str
    name: str
    kind: str
    signature: str
    summary: str
    version_note: str

    def to_dict(self):
        """Convert the record into a dictionary."""
        return asdict(self)
