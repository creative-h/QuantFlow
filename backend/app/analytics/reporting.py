"""Standalone HTML and JSON performance report generators."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
from loguru import logger

from app.analytics.reports import PerformanceReport
from app.paper.portfolio.portfolio import ProfessionalPortfolio


class JSONReportGenerator:
    """Generates structured JSON report exports."""

    @staticmethod
    def generate(portfolio: ProfessionalPortfolio, filepath: Optional[str | Path] = None) -> Dict[str, Any]:
        report = PerformanceReport.generate(portfolio)
        data = report.to_dict()

        # Add trade audit log details
        trades_list = []
        for t in portfolio.trades:
            trades_list.append(
                {
                    "trade_id": t.trade_id,
                    "order_id": t.order_id,
                    "symbol": t.symbol,
                    "side": t.side.value,
                    "quantity": t.quantity,
                    "price": float(t.price),
                    "commission": float(t.commission),
                    "slippage": float(t.slippage),
                    "realized_pnl": float(t.realized_pnl),
                    "timestamp": t.timestamp.isoformat() if t.timestamp else "",
                }
            )

        data["trades"] = trades_list

        if filepath:
            fp = Path(filepath)
            fp.parent.mkdir(parents=True, exist_ok=True)
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info("JSON performance report written to {}", fp)

        return data


class HTMLReportGenerator:
    """Generates standalone, styled HTML performance report documents."""

    @staticmethod
    def generate(
        portfolio: ProfessionalPortfolio,
        title: str = "QuantFlow Performance Report",
        filepath: Optional[str | Path] = None,
    ) -> str:
        rep = PerformanceReport.generate(portfolio)

        trades_html = ""
        for t in portfolio.trades:
            pnl_class = "text-green" if t.realized_pnl > 0 else ("text-red" if t.realized_pnl < 0 else "")
            trades_html += f"""
            <tr>
                <td>{t.timestamp.strftime('%Y-%m-%d %H:%M:%S') if t.timestamp else ''}</td>
                <td>{t.symbol}</td>
                <td><span class="badge badge-{t.side.value.lower()}">{t.side.value}</span></td>
                <td>{t.quantity}</td>
                <td>${float(t.price):,.2f}</td>
                <td>${float(t.commission):,.2f}</td>
                <td class="{pnl_class}">${float(t.realized_pnl):,.2f}</td>
            </tr>
            """

        if not trades_html:
            trades_html = "<tr><td colspan='7' style='text-align:center;'>No trades recorded</td></tr>"

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #38bdf8;
            --green: #22c55e;
            --red: #ef4444;
            --border: #334155;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 30px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{ margin-bottom: 30px; border-bottom: 1px solid var(--border); padding-bottom: 20px; }}
        h1 {{ margin: 0; font-size: 28px; color: var(--accent); }}
        .subtitle {{ color: var(--text-muted); font-size: 14px; margin-top: 5px; }}
        
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .card {{ background: var(--card-bg); border-radius: 10px; padding: 20px; border: 1px solid var(--border); }}
        .card-label {{ color: var(--text-muted); font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }}
        .card-value {{ font-size: 24px; font-weight: bold; margin-top: 8px; }}
        
        .text-green {{ color: var(--green); }}
        .text-red {{ color: var(--red); }}
        
        table {{ width: 100%; border-collapse: collapse; background: var(--card-bg); border-radius: 10px; overflow: hidden; border: 1px solid var(--border); }}
        th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border); font-size: 14px; }}
        th {{ background: #0f172a; color: var(--text-muted); text-transform: uppercase; font-size: 12px; }}
        tr:hover {{ background: #26334d; }}
        
        .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
        .badge-buy {{ background: rgba(34, 197, 94, 0.2); color: var(--green); }}
        .badge-sell {{ background: rgba(239, 68, 68, 0.2); color: var(--red); }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <div class="subtitle">Generated by QuantFlow Quantitative Research Platform</div>
        </header>

        <div class="grid">
            <div class="card">
                <div class="card-label">Total Equity</div>
                <div class="card-value">${rep.total_equity:,.2f}</div>
            </div>
            <div class="card">
                <div class="card-label">Net Profit</div>
                <div class="card-value {'text-green' if rep.net_profit >= 0 else 'text-red'}">${rep.net_profit:,.2f}</div>
            </div>
            <div class="card">
                <div class="card-label">Return %</div>
                <div class="card-value {'text-green' if rep.return_pct >= 0 else 'text-red'}">{rep.return_pct:.2f}%</div>
            </div>
            <div class="card">
                <div class="card-label">Win Rate</div>
                <div class="card-value">{rep.win_rate:.1f}%</div>
            </div>
            <div class="card">
                <div class="card-label">Max Drawdown</div>
                <div class="card-value text-red">{rep.max_drawdown_pct:.2f}%</div>
            </div>
            <div class="card">
                <div class="card-label">Sharpe Ratio</div>
                <div class="card-value">{rep.sharpe_ratio:.2f}</div>
            </div>
            <div class="card">
                <div class="card-label">Profit Factor</div>
                <div class="card-value">{rep.profit_factor:.2f}</div>
            </div>
            <div class="card">
                <div class="card-label">Total Trades</div>
                <div class="card-value">{rep.total_trades}</div>
            </div>
        </div>

        <h2>Trade Execution Log</h2>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Symbol</th>
                    <th>Side</th>
                    <th>Qty</th>
                    <th>Price</th>
                    <th>Comm</th>
                    <th>Realized PnL</th>
                </tr>
            </thead>
            <tbody>
                {trades_html}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

        if filepath:
            fp = Path(filepath)
            fp.parent.mkdir(parents=True, exist_ok=True)
            with open(fp, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info("HTML performance report written to {}", fp)

        return html_content
