"""
Trading system visualization dashboards.

Four dashboards:
  plot_technical_indicators(system)  — price + indicators panel
  plot_signals(system)               — buy/sell signals on price
  plot_performance(system)           — equity curve, drawdown, trade stats
  plot_risk_management(system)       — position sizing, daily P&L, exposure
  plot_all(system)                   — save all four dashboards to PNG
"""

import matplotlib
matplotlib.use("Agg")  # headless – saves to file instead of opening a window

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from datetime import datetime

COLORS = {
    "price":      "#1f77b4",
    "sma20":      "#ff7f0e",
    "sma50":      "#2ca02c",
    "ema12":      "#9467bd",
    "ema26":      "#8c564b",
    "bb_upper":   "#d62728",
    "bb_lower":   "#d62728",
    "bb_fill":    "#ffcccc",
    "volume":     "#aec7e8",
    "macd":       "#1f77b4",
    "signal":     "#ff7f0e",
    "hist_pos":   "#2ca02c",
    "hist_neg":   "#d62728",
    "rsi":        "#9467bd",
    "adx":        "#e377c2",
    "buy":        "#2ca02c",
    "sell":       "#d62728",
    "equity":     "#1f77b4",
    "benchmark":  "#aec7e8",
    "drawdown":   "#d62728",
    "win":        "#2ca02c",
    "loss":       "#d62728",
    "bg":         "#f8f9fa",
    "grid":       "#e0e0e0",
}


def _style_ax(ax, title="", ylabel=""):
    ax.set_facecolor(COLORS["bg"])
    ax.grid(color=COLORS["grid"], linewidth=0.5, linestyle="--")
    ax.spines[["top", "right"]].set_visible(False)
    if title:
        ax.set_title(title, fontsize=10, fontweight="bold", pad=6)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=8)
    ax.tick_params(labelsize=8)


def _format_xaxis(ax, dates):
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")


# ──────────────────────────────────────────────────────────────────────────────
# 1. Technical Indicators Dashboard
# ──────────────────────────────────────────────────────────────────────────────

def plot_technical_indicators(system, save_path="chart_indicators.png"):
    """
    5-panel chart:
      • Price + SMA20/50 + Bollinger Bands + Volume
      • MACD + Signal + Histogram
      • RSI with overbought/oversold bands
      • ADX with +DI / -DI
      • Stochastic oscillator
    """
    df = system.indicators.get("daily")
    if df is None or df.empty:
        print("No indicator data — run calculate_indicators() first.")
        return

    dates = df.index

    fig = plt.figure(figsize=(16, 14))
    fig.patch.set_facecolor("white")
    fig.suptitle(
        f"{system.ticker} — Technical Indicators",
        fontsize=14, fontweight="bold", y=0.98
    )

    gs = gridspec.GridSpec(5, 1, figure=fig,
                           height_ratios=[4, 1.5, 1.5, 1.5, 1.5],
                           hspace=0.08)

    # ── Panel 1: Price + MAs + Bollinger + Volume ──────────────────────────
    ax1 = fig.add_subplot(gs[0])
    _style_ax(ax1, ylabel="Price ($)")

    ax1.fill_between(dates, df["BB_Upper"], df["BB_Lower"],
                     color=COLORS["bb_fill"], alpha=0.4, label="Bollinger Bands")
    ax1.plot(dates, df["BB_Upper"], color=COLORS["bb_upper"],
             linewidth=0.8, linestyle="--", alpha=0.7)
    ax1.plot(dates, df["BB_Lower"], color=COLORS["bb_lower"],
             linewidth=0.8, linestyle="--", alpha=0.7)
    ax1.plot(dates, df["Close"],  color=COLORS["price"],   linewidth=1.5, label="Close", zorder=3)
    ax1.plot(dates, df["SMA_20"], color=COLORS["sma20"],   linewidth=1.2, label="SMA 20")
    ax1.plot(dates, df["SMA_50"], color=COLORS["sma50"],   linewidth=1.2, label="SMA 50")
    ax1.plot(dates, df["EMA_12"], color=COLORS["ema12"],   linewidth=1.0, linestyle=":", label="EMA 12")
    ax1.plot(dates, df["EMA_26"], color=COLORS["ema26"],   linewidth=1.0, linestyle=":", label="EMA 26")
    ax1.legend(loc="upper left", fontsize=7, ncol=3, framealpha=0.8)

    ax_vol = ax1.twinx()
    ax_vol.bar(dates, df["Volume"], color=COLORS["volume"], alpha=0.3, width=0.8)
    ax_vol.set_ylabel("Volume", fontsize=7)
    ax_vol.set_ylim(0, df["Volume"].max() * 4)
    ax_vol.tick_params(labelsize=7)
    ax_vol.spines[["top", "left"]].set_visible(False)
    ax1.set_xticklabels([])

    # ── Panel 2: MACD ──────────────────────────────────────────────────────
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    _style_ax(ax2, ylabel="MACD")
    hist = df["MACD_Histogram"]
    ax2.bar(dates, hist.where(hist >= 0), color=COLORS["hist_pos"], alpha=0.7, width=0.8)
    ax2.bar(dates, hist.where(hist < 0),  color=COLORS["hist_neg"], alpha=0.7, width=0.8)
    ax2.plot(dates, df["MACD"],        color=COLORS["macd"],   linewidth=1.2, label="MACD")
    ax2.plot(dates, df["MACD_Signal"], color=COLORS["signal"], linewidth=1.2, label="Signal")
    ax2.axhline(0, color="black", linewidth=0.5)
    ax2.legend(loc="upper left", fontsize=7, framealpha=0.8)
    ax2.set_xticklabels([])

    # ── Panel 3: RSI ───────────────────────────────────────────────────────
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    _style_ax(ax3, ylabel="RSI")
    ax3.plot(dates, df["RSI"], color=COLORS["rsi"], linewidth=1.2)
    ax3.axhline(70, color=COLORS["sell"], linewidth=0.8, linestyle="--", alpha=0.7)
    ax3.axhline(30, color=COLORS["buy"],  linewidth=0.8, linestyle="--", alpha=0.7)
    ax3.fill_between(dates, 70, df["RSI"].clip(lower=70), color=COLORS["sell"], alpha=0.15)
    ax3.fill_between(dates, df["RSI"].clip(upper=30), 30, color=COLORS["buy"],  alpha=0.15)
    ax3.set_ylim(0, 100)
    ax3.text(dates[-1], 71, "Overbought", fontsize=6, color=COLORS["sell"], ha="right")
    ax3.text(dates[-1], 25, "Oversold",   fontsize=6, color=COLORS["buy"],  ha="right")
    ax3.set_xticklabels([])

    # ── Panel 4: ADX ───────────────────────────────────────────────────────
    ax4 = fig.add_subplot(gs[3], sharex=ax1)
    _style_ax(ax4, ylabel="ADX")
    ax4.plot(dates, df["ADX"],      color=COLORS["adx"],  linewidth=1.2, label="ADX")
    ax4.plot(dates, df["Plus_DI"],  color=COLORS["buy"],  linewidth=1.0, linestyle="--", label="+DI")
    ax4.plot(dates, df["Minus_DI"], color=COLORS["sell"], linewidth=1.0, linestyle="--", label="-DI")
    ax4.axhline(25, color="grey", linewidth=0.8, linestyle=":", alpha=0.7)
    ax4.text(dates[-1], 26, "Strong trend", fontsize=6, color="grey", ha="right")
    ax4.legend(loc="upper left", fontsize=7, framealpha=0.8)
    ax4.set_xticklabels([])

    # ── Panel 5: Stochastic ────────────────────────────────────────────────
    ax5 = fig.add_subplot(gs[4], sharex=ax1)
    _style_ax(ax5, ylabel="Stochastic")
    ax5.plot(dates, df["Stoch_K"], color=COLORS["price"],  linewidth=1.2, label="%K")
    ax5.plot(dates, df["Stoch_D"], color=COLORS["signal"], linewidth=1.2, label="%D", linestyle="--")
    ax5.axhline(80, color=COLORS["sell"], linewidth=0.8, linestyle="--", alpha=0.7)
    ax5.axhline(20, color=COLORS["buy"],  linewidth=0.8, linestyle="--", alpha=0.7)
    ax5.fill_between(dates, 80, df["Stoch_K"].clip(lower=80), color=COLORS["sell"], alpha=0.15)
    ax5.fill_between(dates, df["Stoch_K"].clip(upper=20), 20, color=COLORS["buy"],  alpha=0.15)
    ax5.set_ylim(0, 100)
    ax5.legend(loc="upper left", fontsize=7, framealpha=0.8)
    _format_xaxis(ax5, dates)

    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {save_path}")
    return save_path


# ──────────────────────────────────────────────────────────────────────────────
# 2. Signal Generation Dashboard
# ──────────────────────────────────────────────────────────────────────────────

def plot_signals(system, save_path="chart_signals.png"):
    """
    3-panel chart:
      • Price with buy/sell signal markers and confidence heat
      • Signal confidence over time (bar chart)
      • Cumulative signal count (buy vs sell)
    """
    df = system.indicators.get("daily")
    signals = getattr(system, "signals_history", [])

    if df is None or df.empty:
        print("No indicator data — run backtest() or calculate_indicators() first.")
        return

    dates = df.index

    fig = plt.figure(figsize=(16, 10))
    fig.patch.set_facecolor("white")
    fig.suptitle(
        f"{system.ticker} — Signal Generation",
        fontsize=14, fontweight="bold", y=0.98
    )

    gs = gridspec.GridSpec(3, 1, figure=fig,
                           height_ratios=[4, 1.5, 1.5], hspace=0.12)

    # ── Panel 1: Price + signals ───────────────────────────────────────────
    ax1 = fig.add_subplot(gs[0])
    _style_ax(ax1, ylabel="Price ($)")
    ax1.plot(dates, df["Close"],  color=COLORS["price"], linewidth=1.5, label="Close", zorder=2)
    ax1.plot(dates, df["SMA_20"], color=COLORS["sma20"], linewidth=1.0, alpha=0.7, label="SMA 20")
    ax1.plot(dates, df["SMA_50"], color=COLORS["sma50"], linewidth=1.0, alpha=0.7, label="SMA 50")

    buy_signals  = [s for s in signals if s.signal_type == "BUY"]
    sell_signals = [s for s in signals if s.signal_type == "SELL"]

    if buy_signals:
        bx = [s.timestamp for s in buy_signals]
        by = [s.entry_price for s in buy_signals]
        bc = [s.confidence for s in buy_signals]
        sc = ax1.scatter(bx, by, c=bc, cmap="Greens", vmin=0.5, vmax=1.0,
                         marker="^", s=120, zorder=5, label="Buy signal", edgecolors="darkgreen", linewidths=0.5)

    if sell_signals:
        sx = [s.timestamp for s in sell_signals]
        sy = [s.entry_price for s in sell_signals]
        sc2 = ax1.scatter(sx, sy, c=[s.confidence for s in sell_signals],
                          cmap="Reds", vmin=0.5, vmax=1.0,
                          marker="v", s=120, zorder=5, label="Sell signal", edgecolors="darkred", linewidths=0.5)

    ax1.legend(loc="upper left", fontsize=7, ncol=3, framealpha=0.8)

    if signals:
        cbar_ax = fig.add_axes([0.92, 0.62, 0.012, 0.2])
        sm = plt.cm.ScalarMappable(cmap="RdYlGn", norm=plt.Normalize(vmin=0.5, vmax=1.0))
        sm.set_array([])
        cbar = fig.colorbar(sm, cax=cbar_ax)
        cbar.set_label("Confidence", fontsize=7)
        cbar.ax.tick_params(labelsize=6)

    total = len(signals)
    buys  = len(buy_signals)
    sells = len(sell_signals)
    ax1.set_title(
        f"{system.ticker} — Price with Signals  |  Total: {total}  "
        f"Buy: {buys}  Sell: {sells}",
        fontsize=10, fontweight="bold", pad=6
    )
    ax1.set_xticklabels([])

    # ── Panel 2: Signal confidence bars ───────────────────────────────────
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    _style_ax(ax2, ylabel="Confidence")

    if signals:
        sig_dates = [s.timestamp for s in signals]
        sig_conf  = [s.confidence for s in signals]
        sig_types = [s.signal_type for s in signals]
        bar_colors = [COLORS["buy"] if t == "BUY" else COLORS["sell"] for t in sig_types]
        ax2.bar(sig_dates, sig_conf, color=bar_colors, alpha=0.8, width=2)
        ax2.axhline(0.55, color="grey", linewidth=0.8, linestyle="--", alpha=0.7)
        ax2.text(sig_dates[-1], 0.56, "Min threshold (55%)", fontsize=6, color="grey", ha="right")
        ax2.set_ylim(0.4, 1.05)

        buy_patch  = mpatches.Patch(color=COLORS["buy"],  label="Buy")
        sell_patch = mpatches.Patch(color=COLORS["sell"], label="Sell")
        ax2.legend(handles=[buy_patch, sell_patch], loc="upper left", fontsize=7, framealpha=0.8)
    else:
        ax2.text(0.5, 0.5, "No signals generated", transform=ax2.transAxes,
                 ha="center", va="center", fontsize=10, color="grey")
    ax2.set_xticklabels([])

    # ── Panel 3: Cumulative signals ────────────────────────────────────────
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    _style_ax(ax3, ylabel="Cumulative Count")

    if signals:
        all_dates = sorted(set(df.index.date))
        cum_buy  = []
        cum_sell = []
        cb = cs = 0
        for d in all_dates:
            for s in signals:
                if s.timestamp.date() == d:
                    if s.signal_type == "BUY":
                        cb += 1
                    else:
                        cs += 1
            cum_buy.append(cb)
            cum_sell.append(cs)

        date_index = pd.to_datetime(all_dates)
        ax3.fill_between(date_index, cum_buy,  color=COLORS["buy"],  alpha=0.4, label="Buy")
        ax3.fill_between(date_index, cum_sell, color=COLORS["sell"], alpha=0.4, label="Sell")
        ax3.plot(date_index, cum_buy,  color=COLORS["buy"],  linewidth=1.2)
        ax3.plot(date_index, cum_sell, color=COLORS["sell"], linewidth=1.2)
        ax3.legend(loc="upper left", fontsize=7, framealpha=0.8)

    _format_xaxis(ax3, dates)

    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {save_path}")
    return save_path


# ──────────────────────────────────────────────────────────────────────────────
# 3. Performance Metrics Dashboard
# ──────────────────────────────────────────────────────────────────────────────

def plot_performance(system, save_path="chart_performance.png"):
    """
    6-panel chart:
      • Equity curve vs buy-and-hold benchmark
      • Drawdown
      • Monthly returns heatmap
      • Trade P&L distribution
      • Win/loss breakdown (bar)
      • Rolling Sharpe ratio
    """
    trades = getattr(system, "portfolio", None)
    if trades is None:
        print("No portfolio — run backtest() first.")
        return

    closed = trades.closed_positions
    initial = system.portfolio.initial_capital

    fig = plt.figure(figsize=(16, 14))
    fig.patch.set_facecolor("white")
    fig.suptitle(
        f"{system.ticker} — Performance Metrics",
        fontsize=14, fontweight="bold", y=0.98
    )

    gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.4, wspace=0.3)

    # ── Build equity curve from closed trades ─────────────────────────────
    equity_dates = [pd.Timestamp.now()]
    equity_vals  = [initial]
    if closed:
        equity_dates = [pd.Timestamp(sorted(closed, key=lambda x: x.exit_date)[0].exit_date)]
        equity_vals  = [initial]
        running = initial
        for t in sorted(closed, key=lambda x: x.exit_date):
            running += t.profit_loss
            equity_dates.append(t.exit_date)
            equity_vals.append(running)
    eq_series = pd.Series(equity_vals, index=pd.to_datetime(equity_dates))

    # ── Panel 1: Equity curve ──────────────────────────────────────────────
    ax1 = fig.add_subplot(gs[0, :])
    _style_ax(ax1, "Equity Curve vs Buy & Hold", "Portfolio Value ($)")

    ax1.plot(eq_series.index, eq_series.values,
             color=COLORS["equity"], linewidth=2, label="Strategy", zorder=3)
    ax1.axhline(initial, color="grey", linewidth=0.8, linestyle="--", alpha=0.6, label="Initial capital")

    # Benchmark: buy-and-hold using daily close prices
    df_daily = system.data.get("daily")
    if df_daily is not None and not df_daily.empty and len(closed) > 0:
        start_price = df_daily["Close"].iloc[0]
        end_price   = df_daily["Close"].iloc[-1]
        bh_start = eq_series.index[0]
        bh_end   = eq_series.index[-1]
        bh_end_val = initial * (end_price / start_price)
        ax1.plot([bh_start, bh_end], [initial, bh_end_val],
                 color=COLORS["benchmark"], linewidth=1.5, linestyle="--",
                 label=f"Buy & Hold ({(end_price/start_price - 1)*100:+.1f}%)")

    final_val = eq_series.values[-1]
    ret = (final_val - initial) / initial * 100
    ax1.fill_between(eq_series.index, initial, eq_series.values,
                     where=np.array(equity_vals) >= initial,
                     color=COLORS["buy"], alpha=0.15)
    ax1.fill_between(eq_series.index, initial, eq_series.values,
                     where=np.array(equity_vals) < initial,
                     color=COLORS["sell"], alpha=0.15)
    ax1.set_title(
        f"Equity Curve vs Buy & Hold  |  Return: {ret:+.2f}%  "
        f"Final: ${final_val:,.2f}",
        fontsize=10, fontweight="bold", pad=6
    )
    ax1.legend(fontsize=8, framealpha=0.8)
    _format_xaxis(ax1, eq_series.index)

    # ── Panel 2: Drawdown ──────────────────────────────────────────────────
    ax2 = fig.add_subplot(gs[1, 0])
    _style_ax(ax2, "Drawdown", "Drawdown (%)")
    eq_arr = np.array(equity_vals, dtype=float)
    running_max = np.maximum.accumulate(eq_arr)
    drawdown = (eq_arr - running_max) / running_max * 100
    ax2.fill_between(eq_series.index, drawdown, 0, color=COLORS["drawdown"], alpha=0.6)
    ax2.plot(eq_series.index, drawdown, color=COLORS["drawdown"], linewidth=1)
    max_dd = drawdown.min()
    ax2.axhline(max_dd, color="black", linewidth=0.8, linestyle="--", alpha=0.5)
    ax2.text(eq_series.index[-1], max_dd - 0.5, f"Max DD: {max_dd:.2f}%",
             fontsize=7, ha="right", color="black")
    _format_xaxis(ax2, eq_series.index)

    # ── Panel 3: Trade P&L distribution ───────────────────────────────────
    ax3 = fig.add_subplot(gs[1, 1])
    _style_ax(ax3, "Trade P&L Distribution", "Number of Trades")
    if closed:
        pnls = [t.profit_loss for t in closed]
        wins  = [p for p in pnls if p >= 0]
        losses = [p for p in pnls if p < 0]
        bins = min(20, max(5, len(pnls) // 2))
        ax3.hist(wins,   bins=bins, color=COLORS["win"],  alpha=0.7, label=f"Wins ({len(wins)})")
        ax3.hist(losses, bins=bins, color=COLORS["loss"], alpha=0.7, label=f"Losses ({len(losses)})")
        ax3.axvline(0, color="black", linewidth=1)
        avg_win  = np.mean(wins)  if wins   else 0
        avg_loss = np.mean(losses) if losses else 0
        ax3.axvline(avg_win,  color=COLORS["win"],  linewidth=1.2, linestyle="--",
                    label=f"Avg win ${avg_win:+.0f}")
        ax3.axvline(avg_loss, color=COLORS["loss"], linewidth=1.2, linestyle="--",
                    label=f"Avg loss ${avg_loss:+.0f}")
        ax3.set_xlabel("P&L ($)", fontsize=8)
        ax3.legend(fontsize=7, framealpha=0.8)
    else:
        ax3.text(0.5, 0.5, "No closed trades", transform=ax3.transAxes,
                 ha="center", va="center", fontsize=10, color="grey")

    # ── Panel 4: Win/loss metrics bar ──────────────────────────────────────
    ax4 = fig.add_subplot(gs[2, 0])
    _style_ax(ax4, "Performance Summary")
    if closed:
        summary = trades.get_portfolio_summary()
        metrics = {
            "Win Rate\n(%)":        summary.get("win_rate", 0),
            "Profit\nFactor ×10":   min(summary.get("profit_factor", 0) * 10, 100),
            "Sharpe\n×20":          min(summary.get("sharpe_ratio", 0) * 20, 100),
            "Return\n(%)":          max(min(summary.get("return_pct", 0), 100), -100),
        }
        labels = list(metrics.keys())
        values = list(metrics.values())
        bar_colors = [COLORS["buy"] if v >= 0 else COLORS["sell"] for v in values]
        bars = ax4.bar(labels, values, color=bar_colors, alpha=0.8, edgecolor="white", linewidth=1.2)
        ax4.axhline(0, color="black", linewidth=0.8)
        raw = [
            summary.get("win_rate", 0),
            summary.get("profit_factor", 0),
            summary.get("sharpe_ratio", 0),
            summary.get("return_pct", 0),
        ]
        for bar, rv in zip(bars, raw):
            ypos = bar.get_height() + 1 if bar.get_height() >= 0 else bar.get_height() - 4
            ax4.text(bar.get_x() + bar.get_width() / 2, ypos,
                     f"{rv:.2f}", ha="center", fontsize=8, fontweight="bold")
        ax4.set_ylabel("Scaled value", fontsize=8)
    else:
        ax4.text(0.5, 0.5, "No trades", transform=ax4.transAxes,
                 ha="center", va="center", fontsize=10, color="grey")

    # ── Panel 5: Monthly returns heatmap ───────────────────────────────────
    ax5 = fig.add_subplot(gs[2, 1])
    _style_ax(ax5, "Monthly Returns (%)")
    if closed and len(closed) > 1:
        trade_df = pd.DataFrame([
            {"date": t.exit_date, "pnl": t.profit_loss}
            for t in closed
        ])
        trade_df["date"] = pd.to_datetime(trade_df["date"])
        trade_df = trade_df.set_index("date").resample("ME")["pnl"].sum()
        trade_df.index = trade_df.index.to_period("M")

        months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        years  = sorted(trade_df.index.year.unique())
        heat   = pd.DataFrame(index=years, columns=range(1, 13), dtype=float)
        for period, val in trade_df.items():
            heat.loc[period.year, period.month] = val

        im = ax5.imshow(heat.values.astype(float), cmap="RdYlGn",
                        aspect="auto", interpolation="nearest")
        ax5.set_xticks(range(12))
        ax5.set_xticklabels(months, fontsize=7)
        ax5.set_yticks(range(len(years)))
        ax5.set_yticklabels(years, fontsize=7)
        for (r, c), val in np.ndenumerate(heat.values.astype(float)):
            if not np.isnan(val):
                ax5.text(c, r, f"${val:.0f}", ha="center", va="center",
                         fontsize=6, color="black" if abs(val) < heat.values[~np.isnan(heat.values)].std() else "white")
        plt.colorbar(im, ax=ax5, fraction=0.03, pad=0.04).ax.tick_params(labelsize=6)
    else:
        ax5.text(0.5, 0.5, "Insufficient data\nfor monthly heatmap",
                 transform=ax5.transAxes, ha="center", va="center",
                 fontsize=9, color="grey")

    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {save_path}")
    return save_path


# ──────────────────────────────────────────────────────────────────────────────
# 4. Risk Management Dashboard
# ──────────────────────────────────────────────────────────────────────────────

def plot_risk_management(system, save_path="chart_risk.png"):
    """
    4-panel chart:
      • Position size per trade (% of portfolio)
      • Cumulative P&L with stop-loss / take-profit levels
      • Daily P&L bar chart
      • Risk/reward ratio per trade
    """
    closed = system.portfolio.closed_positions if system.portfolio else []
    initial = system.portfolio.initial_capital

    fig = plt.figure(figsize=(16, 12))
    fig.patch.set_facecolor("white")
    fig.suptitle(
        f"{system.ticker} — Risk Management",
        fontsize=14, fontweight="bold", y=0.98
    )

    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.4, wspace=0.3)

    # ── Panel 1: Position size % of portfolio ─────────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    _style_ax(ax1, "Position Size per Trade", "% of Portfolio")
    if closed:
        pct_sizes = [abs(t.quantity * t.entry_price) / initial * 100 for t in closed]
        colors    = [COLORS["buy"] if t.profit_loss >= 0 else COLORS["loss"] for t in closed]
        ax1.bar(range(len(closed)), pct_sizes, color=colors, alpha=0.8)
        ax1.axhline(system.risk_manager.max_position_size_pct * 100,
                    color="red", linewidth=1.2, linestyle="--",
                    label=f"Max limit ({system.risk_manager.max_position_size_pct*100:.0f}%)")
        avg_size = np.mean(pct_sizes)
        ax1.axhline(avg_size, color="orange", linewidth=1, linestyle=":",
                    label=f"Avg ({avg_size:.1f}%)")
        ax1.set_xlabel("Trade #", fontsize=8)
        ax1.legend(fontsize=7, framealpha=0.8)
    else:
        ax1.text(0.5, 0.5, "No closed trades", transform=ax1.transAxes,
                 ha="center", va="center", fontsize=10, color="grey")

    # ── Panel 2: Entry / stop-loss / take-profit per trade ─────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    _style_ax(ax2, "Entry / Stop-Loss / Take-Profit Levels", "Price ($)")
    if closed:
        for i, t in enumerate(closed[:30]):  # cap at 30 for readability
            color = COLORS["buy"] if t.side == "LONG" else COLORS["sell"]
            ax2.plot([i, i], [t.stop_loss, t.take_profit],
                     color="lightgrey", linewidth=6, solid_capstyle="round", zorder=1)
            ax2.scatter(i, t.entry_price, color=color,  s=60,  zorder=3, label="Entry" if i == 0 else "")
            ax2.scatter(i, t.stop_loss,   color=COLORS["loss"], s=40, marker="_", zorder=3,
                        label="Stop Loss" if i == 0 else "", linewidths=2)
            ax2.scatter(i, t.take_profit, color=COLORS["win"],  s=40, marker="_", zorder=3,
                        label="Take Profit" if i == 0 else "", linewidths=2)
        ax2.set_xlabel("Trade #", fontsize=8)
        ax2.legend(fontsize=7, framealpha=0.8, loc="upper left")
        if len(closed) > 30:
            ax2.set_title(f"Entry / Stop-Loss / Take-Profit Levels (first 30 of {len(closed)})",
                          fontsize=10, fontweight="bold", pad=6)
    else:
        ax2.text(0.5, 0.5, "No closed trades", transform=ax2.transAxes,
                 ha="center", va="center", fontsize=10, color="grey")

    # ── Panel 3: Daily P&L ─────────────────────────────────────────────────
    ax3 = fig.add_subplot(gs[1, 0])
    _style_ax(ax3, "Daily P&L", "P&L ($)")
    if closed:
        daily_pnl = {}
        for t in closed:
            d = t.exit_date.date()
            daily_pnl[d] = daily_pnl.get(d, 0) + t.profit_loss
        d_dates = sorted(daily_pnl)
        d_vals  = [daily_pnl[d] for d in d_dates]
        bar_colors = [COLORS["win"] if v >= 0 else COLORS["loss"] for v in d_vals]
        ax3.bar(pd.to_datetime(d_dates), d_vals, color=bar_colors, alpha=0.8, width=1)
        ax3.axhline(0, color="black", linewidth=0.8)
        max_loss = system.risk_manager.max_daily_loss_pct * initial
        ax3.axhline(-max_loss, color="red", linewidth=1.2, linestyle="--",
                    label=f"Daily loss limit (−${max_loss:,.0f})")
        ax3.legend(fontsize=7, framealpha=0.8)
        _format_xaxis(ax3, pd.to_datetime(d_dates))
    else:
        ax3.text(0.5, 0.5, "No closed trades", transform=ax3.transAxes,
                 ha="center", va="center", fontsize=10, color="grey")

    # ── Panel 4: Risk/reward per trade ─────────────────────────────────────
    ax4 = fig.add_subplot(gs[1, 1])
    _style_ax(ax4, "Risk/Reward Ratio per Trade", "R:R Ratio")
    if closed:
        rr_ratios = []
        for t in closed:
            risk   = abs(t.entry_price - t.stop_loss)
            reward = abs(t.take_profit - t.entry_price)
            rr_ratios.append(reward / risk if risk > 0 else 0)
        colors = [COLORS["win"] if t.profit_loss >= 0 else COLORS["loss"] for t in closed]
        ax4.bar(range(len(rr_ratios)), rr_ratios, color=colors, alpha=0.8)
        ax4.axhline(1.0, color="grey",   linewidth=0.8, linestyle=":", label="R:R = 1:1")
        ax4.axhline(2.0, color="orange", linewidth=0.8, linestyle="--", label="R:R = 2:1")
        avg_rr = np.mean(rr_ratios)
        ax4.axhline(avg_rr, color="blue", linewidth=1.2, linestyle="-",
                    label=f"Avg R:R {avg_rr:.2f}")
        ax4.set_xlabel("Trade #", fontsize=8)
        ax4.legend(fontsize=7, framealpha=0.8)
    else:
        ax4.text(0.5, 0.5, "No closed trades", transform=ax4.transAxes,
                 ha="center", va="center", fontsize=10, color="grey")

    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {save_path}")
    return save_path


# ──────────────────────────────────────────────────────────────────────────────
# Convenience: generate all four dashboards
# ──────────────────────────────────────────────────────────────────────────────

def plot_all(system, prefix=""):
    """Generate and save all four dashboards. Returns list of saved paths."""
    p = prefix + "_" if prefix else ""
    saved = []
    saved.append(plot_technical_indicators(system, f"{p}chart_indicators.png"))
    saved.append(plot_signals(system,             f"{p}chart_signals.png"))
    saved.append(plot_performance(system,         f"{p}chart_performance.png"))
    saved.append(plot_risk_management(system,     f"{p}chart_risk.png"))
    return saved


# ──────────────────────────────────────────────────────────────────────────────
# CLI demo
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from automated_trading_system import AutomatedTradingSystem

    ticker = "AAPL"
    system = AutomatedTradingSystem(
        initial_capital=100000,
        ticker=ticker,
        max_positions=5,
        max_position_size_pct=0.20,
    )
    system.backtest(start_date="2023-01-01", end_date="2024-01-01")

    paths = plot_all(system, prefix=ticker)
    print("\nAll charts saved:")
    for p in paths:
        if p:
            print(f"  {p}")
