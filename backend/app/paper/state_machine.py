"""Trade State Machine managing trade execution state lifecycle."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from loguru import logger


class TradeState(str, Enum):
    """8-State lifecycle for autonomous options trading."""

    WAITING = "WAITING"
    WATCHLIST = "WATCHLIST"
    READY = "READY"
    ENTERED = "ENTERED"
    PARTIAL_EXIT = "PARTIAL_EXIT"
    TRAILING = "TRAILING"
    EXITED = "EXITED"
    REJECTED = "REJECTED"


@dataclass
class StateTransitionLog:
    """Dataclass storing timestamped state transition log."""

    from_state: TradeState
    to_state: TradeState
    timestamp: datetime = field(default_factory=datetime.now)
    reason: str = ""


class TradeStateMachine:
    """State Machine enforcing valid state transitions and maintaining trade lifecycle history."""

    VALID_TRANSITIONS = {
        TradeState.WAITING: [TradeState.WATCHLIST, TradeState.REJECTED],
        TradeState.WATCHLIST: [TradeState.READY, TradeState.WAITING, TradeState.REJECTED],
        TradeState.READY: [TradeState.ENTERED, TradeState.WAITING, TradeState.REJECTED],
        TradeState.ENTERED: [TradeState.PARTIAL_EXIT, TradeState.TRAILING, TradeState.EXITED, TradeState.REJECTED],
        TradeState.PARTIAL_EXIT: [TradeState.TRAILING, TradeState.EXITED],
        TradeState.TRAILING: [TradeState.EXITED],
        TradeState.EXITED: [],
        TradeState.REJECTED: [],
    }

    def __init__(self, trade_id: str, initial_state: TradeState = TradeState.WAITING) -> None:
        self.trade_id = trade_id
        self.current_state = initial_state
        self.history: List[StateTransitionLog] = []

    def transition_to(self, target_state: TradeState, reason: str = "") -> bool:
        """Attempt to transition trade to target state with validation."""
        valid_next_states = self.VALID_TRANSITIONS.get(self.current_state, [])
        if target_state not in valid_next_states:
            logger.warning(
                "Invalid trade state transition attempted for trade {}: {} -> {}",
                self.trade_id,
                self.current_state.value,
                target_state.value,
            )
            return False

        log_entry = StateTransitionLog(
            from_state=self.current_state,
            to_state=target_state,
            timestamp=datetime.now(),
            reason=reason,
        )
        self.history.append(log_entry)
        logger.info(
            "Trade {} state transition: {} -> {} (Reason: {})",
            self.trade_id,
            self.current_state.value,
            target_state.value,
            reason,
        )
        self.current_state = target_state
        return True
