"""The visual state machine for the STARK//CODE gateway experience."""

from enum import Enum, auto
import time


class ExperienceStage(Enum):
    BOOT = auto()
    GATEWAY = auto()
    CASTING = auto()
    SPELL_VERIFIED = auto()
    GATEWAY_OPENING = auto()
    SANCTUM_INITIALIZING = auto()
    PROJECT_INITIALIZING = auto()
    LAUNCHING_VSCODE = auto()
    WORKSPACE_ACTIVE = auto()
    ERROR_PROJECT = auto()
    ERROR_VSCODE = auto()


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
        elif self.stage is ExperienceStage.SPELL_VERIFIED and elapsed >= 1.0:
            self._move_to(ExperienceStage.GATEWAY_OPENING, now)
        elif self.stage is ExperienceStage.GATEWAY_OPENING and elapsed >= 1.25:
            self._move_to(ExperienceStage.SANCTUM_INITIALIZING, now)
        elif self.stage is ExperienceStage.SANCTUM_INITIALIZING and elapsed >= 1.25:
            self._move_to(ExperienceStage.PROJECT_INITIALIZING, now)
        # Project initialization and VS code launching are advanced by the UI querying the worker.

    def verify_spell(self, now: float) -> None:
        if self.stage in (ExperienceStage.GATEWAY, ExperienceStage.CASTING):
            self._move_to(ExperienceStage.SPELL_VERIFIED, now)

    def trigger_next(self, stage: ExperienceStage, now: float) -> None:
        self._move_to(stage, now)

    def progress(self, now: float, duration: float) -> float:
        return max(0.0, min(1.0, (now - self.stage_started) / duration))

    def _move_to(self, stage: ExperienceStage, now: float) -> None:
        self.stage = stage
        self.stage_started = now
