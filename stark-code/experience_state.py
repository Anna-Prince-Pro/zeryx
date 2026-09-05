"""The visual state machine for the STARK//CODE gateway experience."""

from enum import Enum, auto
import time


class ExperienceStage(Enum):
    BOOT = auto()
    GATEWAY = auto()
    CASTING = auto()
    SPELL_VERIFIED = auto()
    PORTAL_OPENING = auto()
    MAIN_ENVIRONMENT = auto()


class ExperienceFlow:
    """Keeps the portal sequence independent from tracking and rendering."""

    def __init__(self) -> None:
        self.stage = ExperienceStage.BOOT
        self.stage_started = time.monotonic()

    def advance(self, now: float, casting: bool) -> None:
        elapsed = now - self.stage_started
        if self.stage is ExperienceStage.BOOT and elapsed >= 0.75:
            self._move_to(ExperienceStage.GATEWAY, now)
        elif self.stage is ExperienceStage.GATEWAY and casting:
            self._move_to(ExperienceStage.CASTING, now)
        elif self.stage is ExperienceStage.CASTING and not casting:
            self._move_to(ExperienceStage.GATEWAY, now)
        elif self.stage is ExperienceStage.SPELL_VERIFIED and elapsed >= 0.62:
            self._move_to(ExperienceStage.PORTAL_OPENING, now)
        elif self.stage is ExperienceStage.PORTAL_OPENING and elapsed >= 1.25:
            self._move_to(ExperienceStage.MAIN_ENVIRONMENT, now)

    def verify_spell(self, now: float) -> None:
        if self.stage is not ExperienceStage.MAIN_ENVIRONMENT:
            self._move_to(ExperienceStage.SPELL_VERIFIED, now)

    def progress(self, now: float, duration: float) -> float:
        return max(0.0, min(1.0, (now - self.stage_started) / duration))

    def _move_to(self, stage: ExperienceStage, now: float) -> None:
        self.stage = stage
        self.stage_started = now
