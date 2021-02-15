from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Iterable, DefaultDict

from fallen_london_chronicler.schema import PossessionInfo


@dataclass
class PossessionState:
    name: str
    level: int
    category: str
    progress_percentage: int
    cap: Optional[int] = None

    @property
    def cp(self):
        total = 0
        cp_cap = 70 if self.category == "BasicAbility" else 50
        for level in range(1, self.level + 1):
            total += min(level, cp_cap)
        total += round(
            self.progress_percentage * min(self.level + 1, cp_cap) / 100
        )
        return total


@dataclass
class RecordingState:
    active: bool = False
    possessions: Dict[Any, Any] = field(default_factory=dict)

    def get_possession(self, quality_id: int) -> Optional[PossessionState]:
        return self.possessions.get(quality_id)

    def update_possessions(
            self, possessions_info: Iterable[PossessionInfo]
    ) -> None:
        self.possessions = {}
        for possession_info in possessions_info:
            self.update_possession(possession_info)

    def update_possession(
            self, possession_info: PossessionInfo
    ) -> PossessionState:
        new_state = PossessionState(
            name=possession_info.name,
            level=possession_info.level,
            category=possession_info.category,
            progress_percentage=possession_info.progressAsPercentage,
            cap=possession_info.cap
        )
        self.possessions[possession_info.id] = new_state
        return new_state


recording_states: DefaultDict[str, RecordingState] = defaultdict(RecordingState)
