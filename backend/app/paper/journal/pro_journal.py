"""Professional Trade Journal storing rich AI decisions, indicators, OI, PCR, and exports."""

import csv
from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from loguru import logger

from app.analytics.multi_agent.decision import AITradeDecision


@dataclass
class ProJournalEntry:
    """Dataclass storing comprehensive telemetry for an executed trade."""

    trade_id: str
    symbol: str
    contract_symbol: str
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: float
    quantity: int
    realized_pnl: float
    duration_seconds: float
    exit_reason: str
    ai_decision: AITradeDecision
    pcr: float = 1.15
    oi_call: int = 150000
    oi_put: int = 180000
    confidence: float = 88.0


class ProTradeJournal:
    """Professional Trade Journal with HTML, JSON, and CSV exporters."""

    def __init__(self, journal_file: Optional[Path] = None) -> None:
        if journal_file is None:
            data_dir = Path(__file__).parent.parent.parent.parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            self.journal_file = data_dir / "pro_trade_journal.json"
        else:
            self.journal_file = Path(journal_file)

        self.entries: List[ProJournalEntry] = []
        self.load()

    def log_trade_entry(self, entry: ProJournalEntry) -> None:
        """Record trade entry in journal."""
        self.entries.append(entry)
        self.save()
        logger.info("Recorded professional trade journal entry for {}", entry.trade_id)

    def save(self) -> None:
        """Persist entries to JSON storage."""
        data = []
        for e in self.entries:
            row = asdict(e)
            row["entry_time"] = e.entry_time.isoformat() if e.entry_time else ""
            row["exit_time"] = e.exit_time.isoformat() if e.exit_time else ""
            row["ai_decision"]["timestamp"] = e.ai_decision.timestamp.isoformat() if e.ai_decision.timestamp else ""
            data.append(row)

        try:
            with open(self.journal_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as err:
            logger.error("Failed to save pro trade journal: {}", str(err))

    def load(self) -> None:
        """Load entries from JSON storage."""
        if not self.journal_file.exists():
            return
        try:
            with open(self.journal_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.entries.clear()
            for row in data:
                # Reconstruct entry
                dec_data = row.pop("ai_decision", {})
                dec_data["timestamp"] = datetime.fromisoformat(dec_data["timestamp"]) if dec_data.get("timestamp") else datetime.now()
                dec_data.pop("agent_opinions", None)
                decision = AITradeDecision(**dec_data)

                row["entry_time"] = datetime.fromisoformat(row["entry_time"]) if row.get("entry_time") else datetime.now()
                row["exit_time"] = datetime.fromisoformat(row["exit_time"]) if row.get("exit_time") else datetime.now()
                row["ai_decision"] = decision
                self.entries.append(ProJournalEntry(**row))
        except Exception as err:
            logger.error("Failed to load pro trade journal: {}", str(err))

    def export_csv(self, filepath: Path) -> Path:
        """Export trade journal history to CSV format."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Trade ID", "Symbol", "Contract", "Entry Time", "Exit Time", "Entry (₹)", "Exit (₹)", "Qty", "PnL (₹)", "Duration (s)", "Exit Reason", "AI Confidence"])
            for e in self.entries:
                writer.writerow([
                    e.trade_id, e.symbol, e.contract_symbol,
                    e.entry_time.strftime("%Y-%m-%d %H:%M:%S") if e.entry_time else "",
                    e.exit_time.strftime("%Y-%m-%d %H:%M:%S") if e.exit_time else "",
                    f"₹{e.entry_price:.2f}", f"₹{e.exit_price:.2f}", e.quantity,
                    f"₹{e.realized_pnl:.2f}", f"{e.duration_seconds:.0f}", e.exit_reason, f"{e.confidence:.1f}%"
                ])
        logger.info("Exported pro trade journal CSV to {}", filepath)
        return filepath

    def export_json(self, filepath: Path) -> Path:
        """Export trade journal history to JSON format."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        self.save()
        with open(self.journal_file, "r", encoding="utf-8") as src, open(filepath, "w", encoding="utf-8") as dst:
            dst.write(src.read())
        logger.info("Exported pro trade journal JSON to {}", filepath)
        return filepath
