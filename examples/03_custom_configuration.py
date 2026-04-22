"""Example 3: Custom Configuration — override risk params and run backtest."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.automated_trading_system import AutomatedTradingSystem

system = AutomatedTradingSystem(
    initial_capital=50000,
    ticker="TSLA",
    max_positions=5,
    max_position_size_pct=0.10,
)

# Tighten daily loss limit
system.risk_manager.max_daily_loss_pct = 0.03

results = system.backtest(start_date="2022-01-01", end_date="2024-01-01")
system.print_detailed_results()

print(f"\nRisk config used:")
print(f"  Max positions:      {system.risk_manager.max_positions}")
print(f"  Max position size:  {system.risk_manager.max_position_size_pct:.0%}")
print(f"  Max daily loss:     {system.risk_manager.max_daily_loss_pct:.0%}")
