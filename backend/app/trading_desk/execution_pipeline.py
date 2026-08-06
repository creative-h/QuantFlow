"""Execution Pipeline Engine tracking live 8-stage trade processing pipeline."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class PipelineStage:
    """Dataclass storing status of a single execution pipeline stage."""

    stage_name: str
    is_active: bool = False
    is_completed: bool = False
    timestamp: Optional[datetime] = None


class ExecutionPipeline:
    """Execution Pipeline Engine tracking stage transitions for live trade processing."""

    DEFAULT_STAGES = [
        "Market Data",
        "Indicator Engine",
        "Multi Agent Analysis",
        "Risk Manager",
        "Trade Approval",
        "Paper Broker",
        "Trade Manager",
        "PnL Engine",
        "Journal",
    ]

    def __init__(self) -> None:
        self.stages: List[PipelineStage] = [
            PipelineStage(stage_name=name, is_completed=True, timestamp=datetime.now()) for name in self.DEFAULT_STAGES
        ]

    def reset_pipeline(self) -> None:
        """Reset pipeline stages for a new trade cycle."""
        for s in self.stages:
            s.is_active = False
            s.is_completed = False
            s.timestamp = None

    def advance_stage(self, stage_name: str) -> None:
        """Mark stage as completed."""
        for s in self.stages:
            if s.stage_name == stage_name:
                s.is_completed = True
                s.is_active = False
                s.timestamp = datetime.now()
            elif not s.is_completed:
                s.is_active = True
                break

    def get_pipeline_status(self) -> List[Dict]:
        """Return pipeline status summary."""
        return [
            {
                "stage": s.stage_name,
                "status": "COMPLETED" if s.is_completed else ("ACTIVE" if s.is_active else "PENDING"),
                "timestamp": s.timestamp.strftime("%H:%M:%S") if s.timestamp else "-",
            }
            for s in self.stages
        ]
