"""
Generate a per-run folder with charts and a Markdown report.

Usage:
    from report import generate_report
    generate_report(system, start_date="2023-01-01", end_date="2024-01-01")

Each call creates:
    runs/<TICKER>_<YYYYMMDD_HHMMSS>/
        report.md
        chart_indicators.png
        chart_signals.png
        chart_performance.png
        chart_risk.png
"""

import os
from datetime import datetime

from visualization import (
    plot_technical_indicators,
    plot_signals,
    plot_performance,
    plot_risk_management,
)


def _run_dir(ticker: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join("runs", f"{ticker}_{ts}")
    os.makedirs(path, exist_ok=True)
    return path


def _stars(value: float, thresholds: tuple, labels: tuple = ("", "★", "★★", "★★★")) -> str:
    for i, t in reversed(list(enumerate(thresholds))):
        if value >= t:
            return labels[i + 1]
    return labels[0]


def generate_report(system, start_date: str = "", end_date: str = "") -> str:
    """
    Generate a full run folder with charts + report.md.
    Returns the path to the folder.
    """
    ticker = system.ticker
    run_path = _run_dir(ticker)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Generate charts ────────────────────────────────────────────────────
    chart_indicators  = os.path.join(run_path, "chart_indicators.png")
    chart_signals     = os.path.join(run_path, "chart_signals.png")
    chart_performance = os.path.join(run_path, "chart_performance.png")
    chart_risk        = os.path.join(run_path, "chart_risk.png")

    plot_technical_indicators(system, chart_indicators)
    plot_signals(system,             chart_signals)
    plot_performance(system,         chart_performance)
    plot_risk_management(system,     chart_risk)

    # ── Gather data ────────────────────────────────────────────────────────
    portfolio  = system.portfolio.get_portfolio_summary()
    trades_stats = system.trade_logger.get_trade_statistics()
    signals_stats = system.signal_generator.get_signal_summary()
    closed = system.portfolio.closed_positions
    df_daily = system.data.get("daily")

    # Date range (fall back to data if not passed in)
    if not start_date and df_daily is not None and not df_daily.empty:
        start_date = str(df_daily.index[0].date())
    if not end_date and df_daily is not None and not df_daily.empty:
        end_date = str(df_daily.index[-1].date())

    ret      = portfolio.get("return_pct", 0)
    win_rate = trades_stats.get("win_rate", 0)
    pf       = trades_stats.get("profit_factor", 0)
    sharpe   = portfolio.get("sharpe_ratio", trades_stats.get("sharpe_ratio", 0))
    max_dd   = _calc_max_drawdown(closed, portfolio["initial_capital"])

    # ── Build Markdown ─────────────────────────────────────────────────────
    lines = []

    lines += [
        f"# Trading System Report — {ticker}",
        "",
        f"**Generated:** {generated_at}  ",
        f"**Period:** {start_date} → {end_date}  ",
        f"**Initial Capital:** ${portfolio['initial_capital']:,.2f}  ",
        f"**Run folder:** `{run_path}`",
        "",
        "---",
        "",
    ]

    # ── Executive summary ──────────────────────────────────────────────────
    lines += [
        "## Executive Summary",
        "",
        f"| Metric | Value | Rating |",
        f"|--------|-------|--------|",
        f"| Final Portfolio Value | ${portfolio['total_value']:,.2f} | |",
        f"| Total Return | {ret:+.2f}% | {_stars(ret, (0, 5, 15))} |",
        f"| Win Rate | {win_rate:.1f}% | {_stars(win_rate, (40, 50, 60))} |",
        f"| Profit Factor | {pf:.2f} | {_stars(pf, (0.8, 1.5, 2.0))} |",
        f"| Max Drawdown | {max_dd:.2f}% | {_stars(-max_dd, (-100, -20, -10))} |",
        f"| Total Trades | {trades_stats.get('total_trades', 0)} | |",
        "",
        "---",
        "",
    ]

    # ── Technical indicators ───────────────────────────────────────────────
    lines += [
        "## Technical Indicators",
        "",
        "Price action with moving averages, Bollinger Bands, volume, MACD, RSI, ADX, and Stochastic oscillator.",
        "",
        f"![Technical Indicators](chart_indicators.png)",
        "",
    ]

    if df_daily is not None and not df_daily.empty:
        ind = system.indicators.get("daily")
        if ind is not None and not ind.empty:
            latest = ind.iloc[-1]
            lines += [
                "### Latest Indicator Values",
                "",
                f"| Indicator | Value | Interpretation |",
                f"|-----------|-------|----------------|",
                f"| Close | ${latest.get('Close', 0):.2f} | |",
                f"| SMA 20 | ${latest.get('SMA_20', 0):.2f} | {'Price above ▲' if latest.get('Close',0) > latest.get('SMA_20',0) else 'Price below ▼'} |",
                f"| SMA 50 | ${latest.get('SMA_50', 0):.2f} | {'Price above ▲' if latest.get('Close',0) > latest.get('SMA_50',0) else 'Price below ▼'} |",
                f"| RSI (14) | {latest.get('RSI', 0):.1f} | {_rsi_label(latest.get('RSI', 50))} |",
                f"| MACD | {latest.get('MACD', 0):.4f} | {'Bullish ▲' if latest.get('MACD',0) > latest.get('MACD_Signal',0) else 'Bearish ▼'} |",
                f"| ADX | {latest.get('ADX', 0):.1f} | {_adx_label(latest.get('ADX', 0))} |",
                f"| ATR | ${latest.get('ATR', 0):.2f} | Daily volatility estimate |",
                "",
            ]

    lines += ["---", ""]

    # ── Signal generation ──────────────────────────────────────────────────
    lines += [
        "## Signal Generation",
        "",
        f"![Signal Generation](chart_signals.png)",
        "",
        "### Signal Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Signals | {signals_stats.get('total_signals', 0)} |",
        f"| Buy Signals | {signals_stats.get('buy_signals', 0)} |",
        f"| Sell Signals | {signals_stats.get('sell_signals', 0)} |",
        f"| Avg Confidence | {signals_stats.get('avg_confidence', 0):.1%} |",
        f"| Min Confidence Threshold | 55.0% |",
        "",
    ]

    # Last 10 signals table
    recent_signals = sorted(system.signals_history, key=lambda s: s.timestamp)[-10:]
    if recent_signals:
        lines += [
            "### Last 10 Signals",
            "",
            "| Date | Type | Price | Stop | Target | Confidence | Reasons |",
            "|------|------|-------|------|--------|------------|---------|",
        ]
        for s in recent_signals:
            reasons = "; ".join(s.reason[:2]) + ("..." if len(s.reason) > 2 else "")
            lines.append(
                f"| {s.timestamp.strftime('%Y-%m-%d')} "
                f"| {'🔺 BUY' if s.signal_type == 'BUY' else '🔻 SELL'} "
                f"| ${s.entry_price:.2f} "
                f"| ${s.stop_loss:.2f} "
                f"| ${s.take_profit:.2f} "
                f"| {s.confidence:.1%} "
                f"| {reasons} |"
            )
        lines += [""]

    lines += ["---", ""]

    # ── Performance metrics ────────────────────────────────────────────────
    lines += [
        "## Performance Metrics",
        "",
        f"![Performance Metrics](chart_performance.png)",
        "",
        "### Portfolio",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Initial Capital | ${portfolio['initial_capital']:,.2f} |",
        f"| Final Value | ${portfolio['total_value']:,.2f} |",
        f"| Cash | ${portfolio['cash']:,.2f} |",
        f"| Realized P&L | ${portfolio.get('realized_pnl', 0):+,.2f} |",
        f"| Unrealized P&L | ${portfolio.get('unrealized_pnl', 0):+,.2f} |",
        f"| Total Return | {ret:+.2f}% |",
        f"| Max Drawdown | {max_dd:.2f}% |",
        "",
        "### Trade Statistics",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Trades | {trades_stats.get('total_trades', 0)} |",
        f"| Winning Trades | {trades_stats.get('winning_trades', 0)} |",
        f"| Losing Trades | {trades_stats.get('losing_trades', 0)} |",
        f"| Win Rate | {win_rate:.1f}% |",
        f"| Profit Factor | {pf:.2f} |",
        f"| Avg Win | ${trades_stats.get('avg_win', 0):+,.2f} |",
        f"| Avg Loss | ${trades_stats.get('avg_loss', 0):+,.2f} |",
        f"| Largest Win | ${trades_stats.get('largest_win', 0):+,.2f} |",
        f"| Largest Loss | ${trades_stats.get('largest_loss', 0):+,.2f} |",
        f"| Avg Holding Days | {trades_stats.get('avg_holding_days', 0):.1f} |",
        "",
        "---",
        "",
    ]

    # ── Risk management ────────────────────────────────────────────────────
    lines += [
        "## Risk Management",
        "",
        f"![Risk Management](chart_risk.png)",
        "",
        "### Risk Parameters",
        "",
        f"| Parameter | Value |",
        f"|-----------|-------|",
        f"| Max Positions | {system.risk_manager.max_positions} |",
        f"| Max Position Size | {system.risk_manager.max_position_size_pct:.0%} of portfolio |",
        f"| Max Daily Loss | {system.risk_manager.max_daily_loss_pct:.0%} of portfolio |",
        f"| Risk per Trade | 2.0% of portfolio |",
        "",
    ]

    if closed:
        rr_ratios = []
        for t in closed:
            risk   = abs(t.entry_price - t.stop_loss)
            reward = abs(t.take_profit - t.entry_price)
            rr_ratios.append(reward / risk if risk > 0 else 0)
        avg_rr = sum(rr_ratios) / len(rr_ratios) if rr_ratios else 0
        avg_size_pct = sum(
            abs(t.quantity * t.entry_price) / portfolio["initial_capital"] * 100
            for t in closed
        ) / len(closed)
        lines += [
            "### Risk Metrics (from closed trades)",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Avg Position Size | {avg_size_pct:.1f}% of portfolio |",
            f"| Avg Risk/Reward Ratio | {avg_rr:.2f} |",
            f"| Max Drawdown | {max_dd:.2f}% |",
            "",
        ]

    lines += ["---", ""]

    # ── Trade log ──────────────────────────────────────────────────────────
    lines += [
        "## Trade Log",
        "",
        "| # | Date | Side | Entry | Exit | Qty | P&L | Return | Days | Result |",
        "|---|------|------|-------|------|-----|-----|--------|------|--------|",
    ]
    for i, t in enumerate(sorted(closed, key=lambda x: x.entry_date), 1):
        result = "✓ WIN" if t.win else "✗ LOSS"
        lines.append(
            f"| {i} "
            f"| {t.exit_date.strftime('%Y-%m-%d') if t.exit_date else '-'} "
            f"| {t.side} "
            f"| ${t.entry_price:.2f} "
            f"| ${t.exit_price:.2f} "
            f"| {t.quantity:.2f} "
            f"| ${t.profit_loss:+.2f} "
            f"| {t.return_pct:+.1f}% "
            f"| {t.holding_days}d "
            f"| {result} |"
        )

    lines += ["", "---", ""]

    # ── Footer ─────────────────────────────────────────────────────────────
    lines += [
        f"*Report generated by automated-trading-systems on {generated_at}*  ",
        f"*GitHub: https://github.com/edwinlau67/automated-trading-systems*",
    ]

    # ── Write report.md ────────────────────────────────────────────────────
    report_path = os.path.join(run_path, "report.md")
    with open(report_path, "w") as f:
        f.write("\n".join(lines))

    print(f"\nRun saved to: {run_path}/")
    print(f"  report.md")
    print(f"  chart_indicators.png")
    print(f"  chart_signals.png")
    print(f"  chart_performance.png")
    print(f"  chart_risk.png")

    return run_path


# ── Helpers ────────────────────────────────────────────────────────────────

def _calc_max_drawdown(closed, initial_capital: float) -> float:
    if not closed:
        return 0.0
    equity = initial_capital
    peak   = initial_capital
    max_dd = 0.0
    for t in sorted(closed, key=lambda x: x.exit_date or datetime.now()):
        equity += t.profit_loss
        if equity > peak:
            peak = equity
        dd = (equity - peak) / peak * 100
        if dd < max_dd:
            max_dd = dd
    return max_dd


def _rsi_label(rsi: float) -> str:
    if rsi >= 70:
        return "Overbought ▼"
    if rsi <= 30:
        return "Oversold ▲"
    if rsi >= 55:
        return "Bullish zone"
    if rsi <= 45:
        return "Bearish zone"
    return "Neutral"


def _adx_label(adx: float) -> str:
    if adx >= 40:
        return "Very strong trend"
    if adx >= 25:
        return "Strong trend"
    if adx >= 15:
        return "Weak trend"
    return "No trend"


# ── CLI demo ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from src.automated_trading_system import AutomatedTradingSystem

    ticker     = "AAPL"
    start_date = "2023-01-01"
    end_date   = "2024-01-01"

    system = AutomatedTradingSystem(
        initial_capital=10000,
        ticker=ticker,
        max_positions=5,
        max_position_size_pct=0.05,
    )
    system.backtest(start_date=start_date, end_date=end_date)

    run_path = generate_report(system, start_date=start_date, end_date=end_date)
    print(f"\nOpen report: {run_path}/report.md")
