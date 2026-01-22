import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy_financial as npf
import pandas as pd

# ============================================================
# STREAMLIT CONFIGURATION
# ============================================================

st.set_page_config(layout="wide")

st.title("AU-E 5-Year Cash Flow Model")
st.write("Baseline vs Robotics Development Scenarios")

# ============================================================
# INPUTS IN EXPANDER (COLLAPSED BY DEFAULT)
# ============================================================

with st.expander("📊 Adjust Assumptions", expanded=False):
    col_base1, col_base2 = st.columns(2)
    col_robotics1, col_robotics2 = st.columns(2)
    
    # --- Baseline inputs ---
    with col_base1:
        st.subheader("Baseline AU-E")
        baseline_jobs = st.slider("Jobs per year", 5, 30, 12, key="baseline_jobs")
        baseline_rev = st.slider("Revenue per job (CAD)", 50_000, 200_000, 120_000, step=5_000, key="baseline_rev")
    
    with col_base2:
        st.subheader("")
        baseline_exp = st.slider("Expense per job (CAD)", 10_000, 100_000, 40_000, step=5_000, key="baseline_exp")
        baseline_shrink = st.slider("Annual shrink rate (%)", -20, 20, -5, key="baseline_shrink") / 100
    
    # --- Robotics inputs ---
    with col_robotics1:
        st.subheader("Robotics Development")
        stage1_cost = st.number_input("Stage 1 cost (CAD)", value=100_000, key="stage1_cost")
        stage1_duration = st.slider("Stage 1 duration (years)", 0.1, 2.0, 0.5, key="stage1_duration")
        stage2_cost = st.number_input("Stage 2 cost (CAD)", value=350_000, key="stage2_cost")
        stage2_duration = st.slider("Stage 2 duration (years)", 0.5, 3.0, 1.5, key="stage2_duration")
    
    with col_robotics2:
        st.subheader("")
        uplift1 = st.slider("Uplift after Stage 1 (%)", 0, 100, 20, key="uplift1") / 100
        uplift2 = st.slider("Uplift after Stage 2 (%)", 0, 200, 50, key="uplift2") / 100
        rev_growth = st.slider("Revenue growth (%)", 0, 20, 2, key="rev_growth") / 100
        exp_reduction = st.slider("Expense reduction (%)", 0, 50, 10, key="exp_reduction") / 100
    
    discount_rate = st.slider("Discount rate for NPV (%)", 0, 20, 8, key="discount_rate") / 100

years = np.arange(0, 6)

# ============================================================
# MODEL FUNCTIONS
# ============================================================

def baseline_cash_flow():
    jobs = baseline_jobs
    flows = []
    for y in years:
        if y > 0:
            jobs *= (1 + baseline_shrink)
        revenue = jobs * baseline_rev
        expenses = jobs * baseline_exp
        flows.append(revenue - expenses)
    return np.array(flows)

def robotics_cash_flow():
    flows = []
    for y in years:
        # job uplift logic
        if y < stage1_duration:
            jobs = baseline_jobs
        elif y < stage2_duration:
            jobs = baseline_jobs * (1 + uplift1)
        else:
            jobs = baseline_jobs * (1 + uplift1 + uplift2)

        revenue = jobs * baseline_rev * (1 + rev_growth)**y
        expenses = jobs * baseline_exp * (1 - exp_reduction)

        dev_cost = 0
        if y < stage1_duration:
            dev_cost += stage1_cost / stage1_duration
        if y < stage2_duration:
            dev_cost += stage2_cost / stage2_duration

        flows.append(revenue - expenses - dev_cost)
    return np.array(flows)

def npv(cashflows, rate):
    return np.sum(cashflows / (1 + rate)**years)

def calculate_irr(cashflows):
    try:
        irr_value = npf.irr(cashflows)
        # Return None if IRR is NaN or inf
        if irr_value is None or np.isnan(irr_value) or np.isinf(irr_value):
            return None
        return irr_value
    except:
        return None

def calculate_payback_period(cashflows):
    """Calculate payback period for robotics investment"""
    cumsum = np.cumsum(cashflows)
    # Find where cumsum crosses zero (investment is recovered)
    for i, val in enumerate(cumsum):
        if val >= 0:
            if i == 0:
                return 0
            # Linear interpolation between points
            prev_val = cumsum[i-1]
            payback = i - 1 + (-prev_val) / (val - prev_val)
            return payback
    return None  # Never breaks even

def calculate_breakeven_year(baseline_cf, robotics_cf):
    """Calculate first year where robotics cumulative CF exceeds baseline"""
    cumsum_baseline = np.cumsum(baseline_cf)
    cumsum_robotics = np.cumsum(robotics_cf)
    
    for i, (base, robo) in enumerate(zip(cumsum_baseline, cumsum_robotics)):
        if robo > base:
            if i == 0:
                return 0
            # Linear interpolation
            base_prev = cumsum_baseline[i-1]
            robo_prev = cumsum_robotics[i-1]
            breakeven = i - 1 + (base_prev - robo_prev) / ((robo - base) - (robo_prev - base_prev))
            return breakeven
    return None  # Never breaks even

def calculate_cumulative_advantage(baseline_cf, robotics_cf):
    """Calculate total cumulative advantage by end of period"""
    return np.sum(robotics_cf) - np.sum(baseline_cf)

def robotics_cash_flow_with_investment():
    """Cash flow for robotics including upfront investment impact"""
    flows = [0]  # Year -1 placeholder (we'll modify year 0)
    for y in years:
        # job uplift logic
        if y < stage1_duration:
            jobs = baseline_jobs
        elif y < stage2_duration:
            jobs = baseline_jobs * (1 + uplift1)
        else:
            jobs = baseline_jobs * (1 + uplift1 + uplift2)

        revenue = jobs * baseline_rev * (1 + rev_growth)**y
        expenses = jobs * baseline_exp * (1 - exp_reduction)

        dev_cost = 0
        if y < stage1_duration:
            dev_cost += stage1_cost / stage1_duration
        if y < stage2_duration:
            dev_cost += stage2_cost / stage2_duration

        flows.append(revenue - expenses - dev_cost)
    
    # Replace first element with negative initial investment for IRR calculation
    flows[0] = -(stage1_cost + stage2_cost)
    return np.array(flows)

# ============================================================
# RUN MODEL
# ============================================================

baseline_cf = baseline_cash_flow()
robotics_cf = robotics_cash_flow()

baseline_npv = npv(baseline_cf, discount_rate)
robotics_npv = npv(robotics_cf, discount_rate)

# For IRR calculation, use investment-based cash flows
robotics_cf_for_irr = robotics_cash_flow_with_investment()

# Baseline IRR doesn't apply (no investment), Robotics IRR shows return on investment
baseline_irr = None
robotics_irr = calculate_irr(robotics_cf_for_irr)

# Calculate payback period
robotics_payback = calculate_payback_period(np.cumsum(robotics_cf))

# Calculate break-even year and cumulative advantage
breakeven_year = calculate_breakeven_year(baseline_cf, robotics_cf)
cumulative_advantage = calculate_cumulative_advantage(baseline_cf, robotics_cf)

# ============================================================
# DISPLAY RESULTS
# ============================================================

# ============================================================
# DISPLAY RESULTS - METRICS & GRAPHS
# ============================================================

# Professional color palette - vibrant and attractive for investors
COLOR_BASELINE = '#0066CC'  # Professional Blue
COLOR_ROBOTICS = '#00C851'  # Vibrant Green

# Function to format y-axis as CAD currency
def format_cad(x, pos):
    if x >= 1_000_000:
        return f"${x/1_000_000:.1f}M"
    elif x >= 1_000:
        return f"${x/1_000:.0f}K"
    else:
        return f"${x:.0f}"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Baseline NPV (CAD)", f"{round(baseline_npv/1000)*1000:,.0f}")
col2.metric("Baseline IRR", "N/A (No Investment)")
col3.metric("Robotics NPV (CAD)", f"{round(robotics_npv/1000)*1000:,.0f}")
col4.metric("Robotics IRR", f"{robotics_irr*100:.1f}%" if robotics_irr else "N/A")

# --- Plot cash flows with enhanced styling ---
fig, ax = plt.subplots(figsize=(13.5, 6))

# Add stage indicators
ax.axvspan(0, stage1_duration, alpha=0.1, color='#FF6B6B', label='Stage 1 Development')
ax.axvspan(stage1_duration, stage2_duration, alpha=0.1, color='#FFA500', label='Stage 2 Development')

ax.plot(years, baseline_cf, label="Baseline", linewidth=4, marker='o', markersize=10, 
        color=COLOR_BASELINE, markerfacecolor=COLOR_BASELINE, markeredgewidth=2, markeredgecolor='white')
ax.plot(years, robotics_cf, label="Robotics", linewidth=4, marker='s', markersize=10, 
        color=COLOR_ROBOTICS, markerfacecolor=COLOR_ROBOTICS, markeredgewidth=2, markeredgecolor='white')
ax.set_title("Annual Cash Flow Comparison", fontsize=18, fontweight='bold', pad=20)
ax.set_xlabel("Year", fontsize=13, fontweight='bold')
ax.set_ylabel("Cash Flow (CAD)", fontsize=13, fontweight='bold')
ax.grid(True, linestyle="--", alpha=0.25, linewidth=0.8)
ax.legend(fontsize=12, loc='best', framealpha=0.98, shadow=True, edgecolor='black')
ax.axhline(y=0, color='#333333', linestyle='-', linewidth=1, alpha=0.7)

# Format axes
ax.yaxis.set_major_formatter(FuncFormatter(format_cad))
ax.set_xticks([0, 1, 2, 3, 4, 5])
ax.set_xticklabels(['Year 0', 'Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5'])

fig.patch.set_facecolor('white')
ax.set_facecolor('#f5f5f5')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
st.pyplot(fig)

# --- Cumulative cash flow with enhanced styling ---
fig2, ax2 = plt.subplots(figsize=(13.5, 6))
cumsum_baseline = np.cumsum(baseline_cf)
cumsum_robotics = np.cumsum(robotics_cf)

# Add stage indicators
ax2.axvspan(0, stage1_duration, alpha=0.1, color='#FF6B6B', label='Stage 1 Development')
ax2.axvspan(stage1_duration, stage2_duration, alpha=0.1, color='#FFA500', label='Stage 2 Development')

ax2.plot(years, cumsum_baseline, label="Baseline", linewidth=4, marker='o', markersize=10, 
         color=COLOR_BASELINE, markerfacecolor=COLOR_BASELINE, markeredgewidth=2, markeredgecolor='white')
ax2.plot(years, cumsum_robotics, label="Robotics", linewidth=4, marker='s', markersize=10, 
         color=COLOR_ROBOTICS, markerfacecolor=COLOR_ROBOTICS, markeredgewidth=2, markeredgecolor='white')
ax2.fill_between(years, cumsum_baseline, alpha=0.15, color=COLOR_BASELINE)
ax2.fill_between(years, cumsum_robotics, alpha=0.15, color=COLOR_ROBOTICS)
ax2.set_title("Cumulative Cash Flow Comparison", fontsize=18, fontweight='bold', pad=20)
ax2.set_xlabel("Year", fontsize=13, fontweight='bold')
ax2.set_ylabel("Cumulative Cash Flow (CAD)", fontsize=13, fontweight='bold')
ax2.grid(True, linestyle="--", alpha=0.25, linewidth=0.8)
ax2.legend(fontsize=12, loc='best', framealpha=0.98, shadow=True, edgecolor='black')
ax2.axhline(y=0, color='#333333', linestyle='-', linewidth=1, alpha=0.7)

# Format axes
ax2.yaxis.set_major_formatter(FuncFormatter(format_cad))
ax2.set_xticks([0, 1, 2, 3, 4, 5])
ax2.set_xticklabels(['Year 0', 'Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5'])

fig2.patch.set_facecolor('white')
ax2.set_facecolor('#f5f5f5')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
plt.tight_layout()
st.pyplot(fig2)

st.info("💡 Tip: Expand the 'Adjust Assumptions' section above to modify model parameters.")

# ============================================================
# SUMMARY METRICS TABLE
# ============================================================

st.markdown("---")
st.header("📈 Summary Metrics")

summary_data = {
    'Metric': ['NPV (5-year)', 'IRR', 'Break-Even Year', 'Cumulative Advantage'],
    'Baseline': [
        f"${round(baseline_npv/1000)*1000:,.0f}",
        "N/A",
        "N/A",
        "—"
    ],
    'Robotics': [
        f"${round(robotics_npv/1000)*1000:,.0f}",
        f"{robotics_irr*100:.1f}%" if robotics_irr else "N/A",
        f"Year {breakeven_year:.1f}" if breakeven_year is not None else "Never",
        f"${cumulative_advantage:,.0f}"
    ]
}

summary_df = pd.DataFrame(summary_data)
st.dataframe(summary_df, use_container_width=True, hide_index=True)

# ============================================================
# KEY INSIGHTS
# ============================================================

st.markdown("---")
st.header("🎯 Key Insights")

col_insights1, col_insights2 = st.columns(2)

with col_insights1:
    st.subheader("Financial Highlights")
    npv_difference = robotics_npv - baseline_npv
    npv_difference_rounded = round(npv_difference/1000)*1000
    
    if npv_difference > 0:
        st.success(f"✅ Robotics generates **${npv_difference_rounded:,.0f}** more NPV than baseline")
    else:
        st.warning(f"⚠️ Robotics generates **${abs(npv_difference_rounded):,.0f}** less NPV than baseline")
    
    if breakeven_year is not None and breakeven_year < 5:
        st.success(f"🎯 Robotics pulls ahead in **Year {breakeven_year:.1f}**")
    
    if cumulative_advantage > 0:
        st.info(f"💰 **${cumulative_advantage:,.0f}** total advantage by Year 5")

with col_insights2:
    st.subheader("Investment Return")
    if robotics_irr:
        st.metric("Robotics IRR", f"{robotics_irr*100:.1f}%", "Annualized return on investment")
    
    total_investment = stage1_cost + stage2_cost
    st.metric("Total Investment", f"${total_investment:,.0f}", f"Invested over {stage2_duration:.1f} years")
    
    year5_robotics = robotics_cf[-1]
    year5_baseline = baseline_cf[-1]
    st.metric("Year 5 Advantage", f"${year5_robotics - year5_baseline:,.0f}", "Annual cash flow improvement")
