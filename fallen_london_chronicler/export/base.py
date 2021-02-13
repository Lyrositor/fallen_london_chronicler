from abc import ABC, abstractmethod

from fallen_london_chronicler.db import Session


class Exporter(ABC):
    @abstractmethod
    def export_all(self, session: Session) -> str:  # pragma: no cover
        raise NotImplementedError
