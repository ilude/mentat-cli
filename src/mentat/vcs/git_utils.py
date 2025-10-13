from dataclasses import dataclass


@dataclass
class StagedFile:
    path: str
    status: str
