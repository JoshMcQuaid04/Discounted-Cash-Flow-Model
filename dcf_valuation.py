import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import yfinance as yf

ticker = "BHP.AX"
company = yf.Ticker(ticker)

cash_flow_statement = company.cashflow

operating_cash_flow = cash_flow_statement.loc["Operating Cash Flow"]
capital_expenditure = cash_flow_statement.loc["Capital Expenditure"]

free_cash_flow = operating_cash_flow + capital_expenditure

print("Operating Cash Flow:")
print(operating_cash_flow)
print("\nCapital Expenditure:")
print(capital_expenditure)
print("\nFree Cash Flow:")
print(free_cash_flow)

free_cash_flow_clean = free_cash_flow.dropna()
free_cash_flow_clean = free_cash_flow_clean.sort_index()

print("\nCleaned, sorted FCF (oldest to newest):")
print(free_cash_flow_clean)

years_of_data = len(free_cash_flow_clean) - 1
total_growth = free_cash_flow_clean.iloc[-1] / free_cash_flow_clean.iloc[0]
average_growth_rate = total_growth ** (1 / years_of_data) - 1

print("\nAverage annual FCF growth rate:", average_growth_rate)

growth_rate = 0.025

print("\nUsing industry-standard GDP-linked growth rate:", growth_rate)
print("(Raw historical CAGR was", average_growth_rate, "- not used, as it's unreliable for a cyclical commodity company)")

most_recent_fcf = free_cash_flow_clean.iloc[-1]
number_of_forecast_years = 5

projected_fcf = []
for year in range(1, number_of_forecast_years + 1):
    forecasted_value = most_recent_fcf * (1 + growth_rate) ** year
    projected_fcf.append(forecasted_value)

print("\nProjected Free Cash Flow, next 5 years:")
for year, value in enumerate(projected_fcf, start=1):
    print(f"Year {year}: {value:,.0f}")

balance_sheet = company.balance_sheet

total_debt = balance_sheet.loc["Total Debt"].iloc[0]
market_cap = company.info["marketCap"]

total_value = total_debt + market_cap
weight_of_equity = market_cap / total_value
weight_of_debt = total_debt / total_value

print("\nTotal debt:", total_debt)
print("Market cap:", market_cap)
print("Weight of equity:", weight_of_equity)
print("Weight of debt:", weight_of_debt)

risk_free_rate = 0.0422
market_return = 0.085
beta = company.info["beta"]

cost_of_equity = risk_free_rate + beta * (market_return - risk_free_rate)

income_statement = company.financials
interest_expense = income_statement.loc["Interest Expense"].iloc[0]
tax_rate = 0.30

cost_of_debt_after_tax = (interest_expense / total_debt) * (1 - tax_rate)

print("\nBeta:", beta)
print("Cost of equity (CAPM):", cost_of_equity)
print("Cost of debt (after-tax):", cost_of_debt_after_tax)

wacc = (weight_of_equity * cost_of_equity) + (weight_of_debt * cost_of_debt_after_tax)

print("\nWACC:", wacc)

discounted_fcf = []
for year, cash_flow in enumerate(projected_fcf, start=1):
    present_value = cash_flow / (1 + wacc) ** year
    discounted_fcf.append(present_value)

print("\nDiscounted (present value) Free Cash Flow:")
for year, value in enumerate(discounted_fcf, start=1):
    print(f"Year {year}: {value:,.0f}")

sum_of_discounted_fcf = sum(discounted_fcf)
print("\nSum of discounted forecast-period cash flows:", f"{sum_of_discounted_fcf:,.0f}")

terminal_growth_rate = 0.025

year_6_fcf = projected_fcf[-1] * (1 + terminal_growth_rate)
terminal_value = year_6_fcf / (wacc - terminal_growth_rate)

discounted_terminal_value = terminal_value / (1 + wacc) ** number_of_forecast_years

print("\nYear 6 FCF (base for terminal value):", f"{year_6_fcf:,.0f}")
print("Terminal value (at end of Year 5):", f"{terminal_value:,.0f}")
print("Discounted terminal value (today's dollars):", f"{discounted_terminal_value:,.0f}")\

enterprise_value = sum_of_discounted_fcf + discounted_terminal_value

cash_and_equivalents = balance_sheet.loc["Cash And Cash Equivalents"].iloc[0]
equity_value = enterprise_value - total_debt + cash_and_equivalents

shares_outstanding = company.info["sharesOutstanding"]
implied_share_price = equity_value / shares_outstanding

current_share_price = company.info["currentPrice"]

print("\nEnterprise value:", f"{enterprise_value:,.0f}")
print("Equity value:", f"{equity_value:,.0f}")
print("Implied share price:", f"{implied_share_price:,.2f}")
print("Current market share price:", current_share_price)

def calculate_dcf_share_price(wacc_input, terminal_growth_input):
    discounted_fcf_list = []
    for year, cash_flow in enumerate(projected_fcf, start=1):
        present_value = cash_flow / (1 + wacc_input) ** year
        discounted_fcf_list.append(present_value)
    sum_discounted_fcf = sum(discounted_fcf_list)

    year_6 = projected_fcf[-1] * (1 + terminal_growth_input)
    tv = year_6 / (wacc_input - terminal_growth_input)
    discounted_tv = tv / (1 + wacc_input) ** number_of_forecast_years

    ev = sum_discounted_fcf + discounted_tv
    eq_value = ev - total_debt + cash_and_equivalents
    share_price = eq_value / shares_outstanding
    return share_price

import pandas as pd

wacc_range = [wacc - 0.01, wacc - 0.005, wacc, wacc + 0.005, wacc + 0.01]
growth_range = [0.015, 0.02, 0.025, 0.03, 0.035]

wacc_labels = [f"{w:.2%}" for w in wacc_range]
growth_labels = [f"{g:.2%}" for g in growth_range]

sensitivity_table = pd.DataFrame(index=wacc_labels, columns=growth_labels)

for w, w_label in zip(wacc_range, wacc_labels):
    for g, g_label in zip(growth_range, growth_labels):
        price = calculate_dcf_share_price(w, g)
        sensitivity_table.loc[w_label, g_label] = round(price, 2)

sensitivity_table.index.name = "WACC"
sensitivity_table.columns.name = "Terminal Growth"

print("\nSensitivity Table (implied share price):")
print(sensitivity_table)

plt.figure(figsize=(10, 6))

sensitivity_values = sensitivity_table.values.astype(float)

plt.imshow(sensitivity_values, cmap="RdYlGn", aspect="auto")

plt.xticks(range(len(growth_labels)), growth_labels)
plt.yticks(range(len(wacc_labels)), wacc_labels)
plt.xlabel("Terminal Growth Rate")
plt.ylabel("WACC")
plt.title("DCF Sensitivity: Implied Share Price ($AUD)")

for i in range(len(wacc_labels)):
    for j in range(len(growth_labels)):
        plt.text(j, i, f"{sensitivity_values[i, j]:.2f}", ha="center", va="center", color="black", fontsize=10)

colorbar = plt.colorbar()
colorbar.set_label("Implied share price ($)")

plt.tight_layout()
plt.savefig("dcf_sensitivity_heatmap.png", dpi=200, bbox_inches="tight")