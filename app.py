"""TraceGap — Business Process Drift & Change Impact Intelligence."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.change_simulator import (  # noqa: E402
    simulate_director_threshold,
    simulate_finance_threshold,
    simulate_security_scope,
)
from src.drift_scoring import FORMULA  # noqa: E402
from src.threshold_detection import DISCLAIMER  # noqa: E402


st.set_page_config(
    page_title="TraceGap | Process Intelligence",
    page_icon="TG",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAV_ITEMS = [
    "Executive Process Health",
    "Process Explorer",
    "Rule Compliance",
    "Drift Intelligence",
    "Transaction Investigator",
    "Threshold Pattern Detection",
    "System Change Analysis",
    "Change Impact Simulator",
    "Recommendations",
]

NAV_LABELS = {
    "Executive Process Health": "01  Executive Process Health",
    "Process Explorer": "02  Process Explorer",
    "Rule Compliance": "03  Rule Compliance",
    "Drift Intelligence": "04  Drift Intelligence",
    "Transaction Investigator": "05  Transaction Investigator",
    "Threshold Pattern Detection": "06  Threshold Patterns",
    "System Change Analysis": "07  System Change Analysis",
    "Change Impact Simulator": "08  Change Impact Simulator",
    "Recommendations": "09  Recommendations",
}

COLORS = {
    "navy": "#172033",
    "blue": "#2B6FF3",
    "cyan": "#2CA6A4",
    "orange": "#E8993A",
    "red": "#D9544D",
    "green": "#2C8A68",
    "slate": "#687387",
    "pale": "#E9EEF6",
}


def apply_style() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700&display=swap');
        :root { --ink:#172033; --muted:#687387; --line:#E1E7EF; --blue:#2B6FF3; }
        html, body, [class*="css"] { font-family:'DM Sans', sans-serif; color:var(--ink); }
        .stApp { background:linear-gradient(180deg,#F7F9FC 0%,#F4F6F9 100%); }
        [data-testid="stSidebar"] { background:#111A2B; border-right:0; }
        [data-testid="stSidebar"] * { color:#E8EDF6; }
        [data-testid="stSidebar"] .stRadio label { padding:.42rem .5rem; border-radius:8px; }
        [data-testid="stSidebar"] .stRadio label:hover { background:#1B2941; }
        [data-testid="stSidebar"] hr { border-color:#2A3850; }
        [data-testid="stHeader"] { background:rgba(247,249,252,.88); }
        .block-container { padding-top:2.1rem; padding-bottom:4rem; max-width:1500px; }
        h1,h2,h3 { font-family:'Manrope',sans-serif; letter-spacing:-.025em; }
        h1 { font-size:2.25rem !important; font-weight:700 !important; }
        h2 { font-size:1.28rem !important; font-weight:700 !important; }
        h3 { font-size:1rem !important; font-weight:700 !important; }
        .brand { display:flex; align-items:center; gap:12px; margin:4px 0 18px; }
        .brand-mark { display:grid;place-items:center;width:38px;height:38px;border-radius:10px;
            background:linear-gradient(135deg,#4D8BFF,#2CA6A4);font-family:'Manrope';font-weight:800;color:white; }
        .brand-name { font-family:'Manrope';font-size:1.2rem;font-weight:700;color:white; }
        .brand-sub { font-size:.67rem;color:#9EABC0;letter-spacing:.12em;text-transform:uppercase; }
        .eyebrow { color:#2B6FF3;font-size:.72rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;margin-bottom:.4rem; }
        .page-lede { color:#657187;font-size:1.02rem;max-width:850px;margin-top:-.5rem;margin-bottom:1.5rem;line-height:1.55; }
        .metric-card { background:#fff;border:1px solid #E1E7EF;border-radius:14px;padding:17px 18px;min-height:118px;
            box-shadow:0 1px 2px rgba(21,35,58,.03); }
        .metric-label { color:#6B768A;font-size:.69rem;font-weight:700;text-transform:uppercase;letter-spacing:.09em; }
        .metric-value { color:#172033;font-family:'Manrope';font-size:1.8rem;font-weight:700;margin:.35rem 0 .15rem;white-space:nowrap; }
        .metric-note { color:#7D8798;font-size:.75rem;line-height:1.35; }
        .finding-card { background:white;border:1px solid #E1E7EF;border-left:4px solid #2B6FF3;border-radius:12px;
            padding:16px 18px;margin-bottom:10px; }
        .finding-title { font-family:'Manrope';font-weight:700;font-size:.94rem;margin-bottom:5px; }
        .finding-evidence { color:#5F6B7E;font-size:.86rem;line-height:1.5; }
        .info-strip { background:#EAF2FF;border:1px solid #CFE0FF;border-radius:12px;padding:13px 16px;color:#24416F;font-size:.86rem; }
        .warning-strip { background:#FFF7E8;border:1px solid #F2D89A;border-radius:12px;padding:13px 16px;color:#6D4D15;font-size:.86rem; }
        .success-strip { background:#EAF7F2;border:1px solid #C6E7D9;border-radius:12px;padding:13px 16px;color:#215E49;font-size:.86rem; }
        .section-label { color:#34425A;font-family:'Manrope';font-size:1.02rem;font-weight:700;margin:1.15rem 0 .55rem; }
        .path-box { background:white;border:1px solid #E1E7EF;border-radius:14px;padding:18px;margin:8px 0 14px; }
        .path-label { font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;font-weight:700;color:#6B768A;margin-bottom:12px; }
        .step { display:inline-block;background:#EEF3F9;color:#273650;border:1px solid #DCE4EF;padding:7px 10px;border-radius:8px;margin:3px 2px;font-size:.78rem;font-weight:600; }
        .step.missing { background:#FFF0EF;color:#A93F39;border-color:#F1C9C6;text-decoration:line-through; }
        .step.actual { background:#EAF2FF;color:#2455A6;border-color:#C9DCFF; }
        .arrow { color:#9BA6B7;padding:0 2px; }
        .severity-Critical,.severity-High,.severity-Medium,.severity-Low { display:inline-block;padding:3px 8px;border-radius:99px;font-size:.67rem;font-weight:700; }
        .severity-Critical { background:#FDECEB;color:#A93F39; }.severity-High { background:#FFF1E7;color:#A85A1B; }
        .severity-Medium { background:#FFF8DF;color:#856B13; }.severity-Low { background:#EAF7F2;color:#27664F; }
        .recommendation { background:white;border:1px solid #E1E7EF;border-radius:14px;padding:18px;margin-bottom:12px; }
        .rec-id { color:#2B6FF3;font-size:.68rem;font-weight:800;letter-spacing:.1em; }
        .rec-title { font-family:'Manrope';font-size:1.02rem;font-weight:700;margin:5px 0 10px; }
        .rec-grid { display:grid;grid-template-columns:1fr 1fr;gap:12px; }
        .rec-item b { display:block;color:#69758A;text-transform:uppercase;letter-spacing:.08em;font-size:.64rem;margin-bottom:3px; }
        .rec-item { color:#39465B;font-size:.82rem;line-height:1.45; }
        div[data-testid="stDataFrame"] { border:1px solid #E1E7EF;border-radius:12px;overflow:hidden; }
        div[data-testid="stPlotlyChart"] { background:white;border:1px solid #E1E7EF;border-radius:14px;padding:8px; }
        .stButton button { background:#2B6FF3;color:white;border:0;border-radius:9px;font-weight:700; }
        .small-muted { color:#8290A4;font-size:.73rem;line-height:1.45; }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data
def load_data() -> dict[str, object]:
    processed = ROOT / "data" / "processed"
    raw = ROOT / "data" / "raw"
    requests = pd.read_csv(processed / "requests_enriched.csv", parse_dates=["request_date"])
    processes = pd.read_csv(processed / "process_instances.csv")
    violations = pd.read_csv(processed / "rule_violations.csv")
    rule_summary = pd.read_csv(processed / "rule_summary.csv")
    variants = pd.read_csv(processed / "path_variants.csv")
    patterns = pd.read_csv(processed / "threshold_patterns.csv", parse_dates=["first_date", "last_date"])
    events = pd.read_csv(raw / "event_log.csv", parse_dates=["event_timestamp"])
    rules = pd.read_csv(raw / "business_rules.csv")
    with (processed / "metrics.json").open(encoding="utf-8") as handle:
        metric_payload = json.load(handle)
    analysis = requests.merge(processes, on="request_id", validate="one_to_one")
    return {
        "requests": requests, "processes": processes, "analysis": analysis,
        "violations": violations, "rule_summary": rule_summary, "variants": variants,
        "patterns": patterns, "events": events, "rules": rules,
        "summary": metric_payload["summary"], "findings": metric_payload["findings"],
    }


def page_header(eyebrow: str, title: str, lede: str) -> None:
    st.markdown(f'<div class="eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="page-lede">{lede}</div>', unsafe_allow_html=True)


def metric_card(label: str, value: str, note: str) -> None:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
        unsafe_allow_html=True,
    )


def chart_style(fig: go.Figure, height: int = 370) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=18, r=18, t=52, b=18),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="DM Sans", color=COLORS["navy"], size=12),
        title_font=dict(family="Manrope", size=16, color=COLORS["navy"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    fig.update_xaxes(showgrid=False, linecolor="#E5EAF1")
    fig.update_yaxes(gridcolor="#EDF1F6", zeroline=False)
    return fig


def money(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:,.0f}"


def path_html(path: str, mode: str = "actual", missing: set[str] | None = None) -> str:
    missing = missing or set()
    steps = [x.strip() for x in path.split("→")]
    rendered = []
    for i, step in enumerate(steps):
        css = "missing" if step in missing else mode
        rendered.append(f'<span class="step {css}">{step}</span>')
        if i < len(steps) - 1:
            rendered.append('<span class="arrow">→</span>')
    return "".join(rendered)


def executive_page(data: dict[str, object]) -> None:
    summary = data["summary"]
    analysis: pd.DataFrame = data["analysis"]
    findings: list[dict] = data["findings"]
    page_header(
        "Control room / enterprise view",
        "Executive Process Health",
        "A governed view of where Northstar's documented Purchase-to-Pay controls align with—and diverge from—observed system behavior.",
    )
    cols = st.columns(6)
    cards = [
        ("Process alignment", f"{summary['process_alignment_rate']:.1f}%", "Requests meeting every applicable rule"),
        ("Average drift", f"{summary['average_process_drift_score']:.1f}", "Explainable score on a 0–100 scale"),
        ("Critical violations", f"{summary['critical_violations']:,}", "Violation records requiring priority review"),
        ("High violations", f"{summary['high_violations']:,}", "High-severity control exceptions"),
        ("Exception rate", f"{summary['exception_rate']:.1f}%", "Requests using approved exception routing"),
        ("Median cycle", f"{summary['median_approval_cycle_time_hours']:.1f}h", "Submission to terminal workflow event"),
    ]
    for col, card in zip(cols, cards):
        with col:
            metric_card(*card)

    analysis = analysis.copy()
    analysis["month"] = analysis.request_date.dt.to_period("M").dt.to_timestamp()
    trend = analysis.groupby("month", as_index=False).agg(
        alignment_rate=("aligned", lambda s: s.mean() * 100),
        average_drift=("drift_score", "mean"),
        requests=("request_id", "size"),
    )
    left, right = st.columns([1.55, 1])
    with left:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trend.month, y=trend.alignment_rate, mode="lines+markers", name="Alignment rate", line=dict(color=COLORS["blue"], width=3)))
        fig.add_vline(x=pd.Timestamp("2025-07-01").timestamp() * 1000, line_dash="dot", line_color=COLORS["orange"], annotation_text="NovaProcure go-live", annotation_position="top left")
        fig.update_yaxes(title="Alignment rate", ticksuffix="%", range=[max(0, trend.alignment_rate.min() - 5), 100])
        fig.update_layout(title="Process alignment over time")
        st.plotly_chart(chart_style(fig, 360), width="stretch")
    with right:
        period = analysis.groupby("system_period", as_index=False).agg(alignment=("aligned", lambda s: s.mean() * 100), drift=("drift_score", "mean"))
        fig = px.bar(period, x="system_period", y="alignment", color="system_period", category_orders={"system_period": ["Before update", "After update"]}, color_discrete_map={"Before update": COLORS["slate"], "After update": COLORS["blue"]}, text_auto=".1f", title="Before vs after alignment")
        fig.update_traces(texttemplate="%{y:.1f}%", textposition="outside")
        fig.update_yaxes(range=[0, 100], ticksuffix="%", title=None)
        fig.update_xaxes(title=None)
        fig.update_layout(showlegend=False)
        st.plotly_chart(chart_style(fig, 360), width="stretch")

    st.markdown('<div class="section-label">Signals requiring attention</div>', unsafe_allow_html=True)
    for finding in findings[:5]:
        st.markdown(
            f'<div class="finding-card"><div class="finding-title">{finding["title"]}</div>'
            f'<div class="finding-evidence">{finding["evidence"]}</div></div>',
            unsafe_allow_html=True,
        )
    st.markdown('<div class="info-strip"><b>Interpretation:</b> This case study uses synthetic enterprise data. Counts are computed from the generated event log and do not describe a real company or implemented outcome.</div>', unsafe_allow_html=True)


def filter_analysis(analysis: pd.DataFrame, prefix: str) -> pd.DataFrame:
    with st.expander("Filter analysis population", expanded=False):
        c1, c2, c3 = st.columns(3)
        departments = c1.multiselect("Department", sorted(analysis.department_name.unique()), key=f"{prefix}_dept")
        categories = c2.multiselect("Purchase category", sorted(analysis.purchase_type.unique()), key=f"{prefix}_cat")
        risks = c3.multiselect("Risk level", sorted(analysis.risk_category.unique()), key=f"{prefix}_risk")
        c4, c5 = st.columns(2)
        amount = c4.slider("Amount range", 0, int(analysis.amount.max()), (0, 75_000), step=1_000, key=f"{prefix}_amt")
        dates = c5.date_input("Request date", (analysis.request_date.min().date(), analysis.request_date.max().date()), key=f"{prefix}_date")
    filtered = analysis[analysis.amount.between(*amount)]
    if departments:
        filtered = filtered[filtered.department_name.isin(departments)]
    if categories:
        filtered = filtered[filtered.purchase_type.isin(categories)]
    if risks:
        filtered = filtered[filtered.risk_category.isin(risks)]
    if isinstance(dates, (tuple, list)) and len(dates) == 2:
        filtered = filtered[filtered.request_date.dt.date.between(dates[0], dates[1])]
    return filtered


def process_explorer_page(data: dict[str, object]) -> None:
    analysis: pd.DataFrame = data["analysis"]
    page_header("Observed behavior / path variants", "Process Explorer", "Explore how purchases actually moved through enterprise applications and compare the dominant workflow variants across business dimensions.")
    filtered = filter_analysis(analysis, "explore")
    if filtered.empty:
        st.warning("No requests match the selected filters.")
        return
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Filtered requests", f"{len(filtered):,}", "Current analysis population")
    with c2: metric_card("Distinct paths", f"{filtered.observed_path.nunique():,}", "Observed workflow variants")
    with c3: metric_card("Rework rate", f"{(filtered.rework_count > 0).mean()*100:.1f}%", "At least one return-for-revision loop")
    with c4: metric_card("Skipped-step rate", f"{(filtered.missing_steps != '[]').mean()*100:.1f}%", "Expected path contains absent steps")

    paths = filtered.groupby("observed_path", as_index=False).agg(requests=("request_id", "size"), average_drift=("drift_score", "mean"), cycle_hours=("cycle_time_hours", "mean"), total_value=("amount", "sum")).sort_values("requests", ascending=False).head(12)
    paths["short_path"] = paths.observed_path.str.slice(0, 92) + paths.observed_path.apply(lambda x: "…" if len(x) > 92 else "")
    left, right = st.columns([1.4, 1])
    with left:
        fig = px.bar(paths.sort_values("requests"), y="short_path", x="requests", orientation="h", color="average_drift", color_continuous_scale=["#DDE9FF", COLORS["blue"], COLORS["red"]], title="Most common observed paths", hover_data={"observed_path": True, "cycle_hours": ":.1f", "short_path": False})
        fig.update_yaxes(title=None)
        fig.update_xaxes(title="Requests")
        st.plotly_chart(chart_style(fig, 510), width="stretch")
    with right:
        dept = filtered.groupby("department_name", as_index=False).agg(paths=("observed_path", "nunique"), rework_rate=("rework_count", lambda s: (s > 0).mean() * 100), requests=("request_id", "size"))
        fig = px.scatter(dept, x="paths", y="rework_rate", size="requests", color="department_name", title="Variant complexity vs rework", labels={"paths": "Distinct paths", "rework_rate": "Rework rate"})
        fig.update_yaxes(ticksuffix="%")
        fig.update_layout(showlegend=False)
        st.plotly_chart(chart_style(fig, 510), width="stretch")

    st.markdown('<div class="section-label">Variant register</div>', unsafe_allow_html=True)
    display = paths[["observed_path", "requests", "average_drift", "cycle_hours", "total_value"]].copy()
    display.columns = ["Observed workflow path", "Requests", "Avg drift", "Avg cycle (h)", "Transaction value"]
    st.dataframe(display, width="stretch", hide_index=True, column_config={"Transaction value": st.column_config.NumberColumn(format="$%,.0f"), "Avg drift": st.column_config.NumberColumn(format="%.1f"), "Avg cycle (h)": st.column_config.NumberColumn(format="%.1f")})


def rule_compliance_page(data: dict[str, object]) -> None:
    rule_summary: pd.DataFrame = data["rule_summary"]
    violations: pd.DataFrame = data["violations"]
    requests: pd.DataFrame = data["requests"]
    page_header("Policy controls / conformance", "Rule Compliance", "See which business rules apply, how consistently the workflow enforced them, and which transactions require drill-down review.")
    severity_filter = st.multiselect("Severity", ["Critical", "High", "Medium", "Low"], default=["Critical", "High", "Medium", "Low"])
    shown = rule_summary[rule_summary.severity.isin(severity_filter)].sort_values("compliance_pct")
    fig = px.bar(shown, x="compliance_pct", y="rule_name", orientation="h", color="severity", color_discrete_map={"Critical": COLORS["red"], "High": COLORS["orange"], "Medium": "#D3AF35", "Low": COLORS["green"]}, hover_data=["rule_id", "applicable_transactions", "violations", "affected_value"], title="Control compliance by business rule")
    fig.update_xaxes(range=[max(0, shown.compliance_pct.min() - 5), 100], ticksuffix="%", title="Compliance")
    fig.update_yaxes(title=None, categoryorder="total descending")
    st.plotly_chart(chart_style(fig, 565), width="stretch")

    selected = st.selectbox("Inspect a rule", shown.rule_id.tolist(), format_func=lambda rule_id: f"{rule_id} · {shown.set_index('rule_id').loc[rule_id, 'rule_name']}")
    record = rule_summary.set_index("rule_id").loc[selected]
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Applicable", f"{record.applicable_transactions:,.0f}", "Requests that triggered this policy")
    with c2: metric_card("Violations", f"{record.violations:,.0f}", f"{record.severity} severity")
    with c3: metric_card("Compliance", f"{record.compliance_pct:.1f}%", "Applicable requests without violation")
    with c4: metric_card("Gross affected value", money(record.affected_value), "Exposure, not estimated loss")
    st.markdown(f'<div class="info-strip"><b>{selected} — {record.rule_name}:</b> {record.rule_description}</div>', unsafe_allow_html=True)
    detail = violations[violations.rule_id == selected].merge(requests[["request_id", "request_date", "department_name", "employee_id", "vendor_name", "amount", "purchase_type"]], on="request_id")
    st.dataframe(detail[["request_id", "request_date", "department_name", "purchase_type", "amount", "violation_type", "evidence"]], width="stretch", hide_index=True, column_config={"amount": st.column_config.NumberColumn("Amount", format="$%,.0f")})


def drift_intelligence_page(data: dict[str, object]) -> None:
    analysis: pd.DataFrame = data["analysis"].copy()
    page_header("Explainable risk lens / 0–100", "Drift Intelligence", "Prioritize deviation with a transparent score built from policy severity, sequence anomalies, rework, exceptions, and rare-path signals—not machine learning.")
    st.markdown(f'<div class="info-strip"><b>Score formula:</b> {FORMULA}.</div>', unsafe_allow_html=True)
    dept = analysis.groupby("department_name", as_index=False).agg(average_drift=("drift_score", "mean"), alignment_rate=("aligned", lambda s: s.mean() * 100), requests=("request_id", "size"))
    analysis["month"] = analysis.request_date.dt.to_period("M").dt.to_timestamp()
    monthly = analysis.groupby("month", as_index=False).agg(average_drift=("drift_score", "mean"))
    left, right = st.columns(2)
    with left:
        fig = px.bar(dept.sort_values("average_drift"), x="average_drift", y="department_name", orientation="h", color="average_drift", color_continuous_scale=["#DDE9FF", COLORS["blue"], COLORS["red"]], title="Average drift by department", hover_data=["alignment_rate", "requests"])
        fig.update_yaxes(title=None)
        st.plotly_chart(chart_style(fig, 430), width="stretch")
    with right:
        fig = px.line(monthly, x="month", y="average_drift", markers=True, title="Average drift over time", color_discrete_sequence=[COLORS["blue"]])
        fig.add_vline(x=pd.Timestamp("2025-07-01").timestamp() * 1000, line_dash="dot", line_color=COLORS["orange"])
        fig.update_yaxes(title="Drift score")
        fig.update_traces(line_width=3)
        st.plotly_chart(chart_style(fig, 430), width="stretch")

    c1, c2 = st.columns(2)
    with c1:
        category = analysis.groupby("purchase_type", as_index=False).agg(average_drift=("drift_score", "mean"), requests=("request_id", "size")).sort_values("average_drift", ascending=False)
        fig = px.bar(category, x="purchase_type", y="average_drift", color_discrete_sequence=[COLORS["cyan"]], title="Highest-drift purchase categories")
        fig.update_xaxes(title=None)
        st.plotly_chart(chart_style(fig, 370), width="stretch")
    with c2:
        vendor = analysis.groupby(["vendor_id", "vendor_name"], as_index=False).agg(average_drift=("drift_score", "mean"), requests=("request_id", "size")).query("requests >= 20").nlargest(10, "average_drift")
        fig = px.bar(vendor.sort_values("average_drift"), x="average_drift", y="vendor_name", orientation="h", color_discrete_sequence=[COLORS["orange"]], title="Highest-drift vendors (20+ requests)")
        fig.update_yaxes(title=None)
        st.plotly_chart(chart_style(fig, 370), width="stretch")
    st.markdown('<div class="section-label">Priority transaction queue</div>', unsafe_allow_html=True)
    queue = analysis.nlargest(50, ["drift_score", "amount"])[["request_id", "department_name", "purchase_type", "vendor_name", "amount", "drift_score", "violation_count", "observed_path"]]
    st.dataframe(queue, width="stretch", hide_index=True, column_config={"amount": st.column_config.NumberColumn("Amount", format="$%,.0f"), "drift_score": st.column_config.ProgressColumn("Drift score", min_value=0, max_value=100, format="%d")})


def transaction_investigator_page(data: dict[str, object]) -> None:
    analysis: pd.DataFrame = data["analysis"]
    violations: pd.DataFrame = data["violations"]
    events: pd.DataFrame = data["events"]
    page_header("Case-level trace / expected vs observed", "Transaction Investigator", "Select any request to reconstruct its path, identify missing controls, and trace each flag to the policy evidence that produced it.")
    default_id = analysis.sort_values(["drift_score", "amount"], ascending=False).request_id.iloc[0]
    query = st.text_input("Find a request", value=default_id, placeholder="PR-10482").strip().upper()
    matches = analysis[analysis.request_id.str.contains(query, regex=False)] if query else analysis.head(100)
    request_id = st.selectbox("Request", matches.request_id.tolist() if not matches.empty else [default_id])
    row = analysis.set_index("request_id").loc[request_id]
    request_violations = violations[violations.request_id == request_id]
    request_events = events[events.request_id == request_id].sort_values("event_timestamp")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: metric_card("Request", request_id, row.department_name)
    with c2: metric_card("Amount", money(row.amount), row.purchase_type)
    with c3: metric_card("Drift score", f"{row.drift_score:.0f}", "0 aligned · 100 severe deviation")
    with c4: metric_card("Violations", f"{len(request_violations)}", f"{int(row.critical_violation_count)} critical")
    with c5: metric_card("Cycle time", f"{row.cycle_time_hours:.1f}h", row.final_status)

    missing_raw = json.loads(row.missing_steps)
    missing_display = {x.replace("Request Submitted", "Submitted").replace("Manager Approval", "Manager").replace("Director Approval", "Director").replace("Finance Approval", "Finance").replace("Procurement Review", "Procurement").replace("Security Review", "Security").replace("Legal Review", "Legal").replace("Purchase Order Created", "PO Created").replace("Payment Authorized", "Payment") for x in missing_raw}
    st.markdown(f'<div class="path-box"><div class="path-label">Expected process</div>{path_html(row.expected_path, "expected", missing_display)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="path-box"><div class="path-label">Actual process</div>{path_html(row.observed_path, "actual")}</div>', unsafe_allow_html=True)
    if request_violations.empty:
        st.markdown('<div class="success-strip"><b>Aligned:</b> No rule violations were detected for this request.</div>', unsafe_allow_html=True)
    else:
        for violation in request_violations.itertuples():
            st.markdown(f'<div class="finding-card"><span class="severity-{violation.severity}">{violation.severity}</span><div class="finding-title" style="margin-top:8px">{violation.rule_id} · {violation.rule_name}</div><div class="finding-evidence"><b>{violation.violation_type}:</b> {violation.evidence}</div></div>', unsafe_allow_html=True)
    with st.expander("View full event audit trail"):
        st.dataframe(request_events[["event_timestamp", "activity", "performed_by", "performer_role", "system", "previous_status", "new_status"]], width="stretch", hide_index=True)


def threshold_page(data: dict[str, object]) -> None:
    patterns: pd.DataFrame = data["patterns"]
    page_header("Review indicators / threshold proximity", "Potential Threshold Avoidance Patterns", "Detect clusters of repeated, near-threshold transactions submitted by the same employee to the same vendor within a short period.")
    st.markdown(f'<div class="warning-strip"><b>Human review required:</b> {DISCLAIMER}</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: metric_card("Patterns", f"{len(patterns)}", "Employee/vendor clusters")
    with c2: metric_card("Transactions", f"{patterns.transaction_count.sum():.0f}", "Requests inside flagged clusters")
    with c3: metric_card("Combined value", money(patterns.combined_value.sum()), "Review population, not loss")
    fig = px.scatter(patterns, x="first_date", y="combined_value", size="transaction_count", color="department_name", hover_name="pattern_id", hover_data=["employee_id", "vendor_name", "request_ids"], title="Flagged clusters by date and combined value")
    fig.add_hline(y=10_000, line_dash="dot", line_color=COLORS["orange"], annotation_text="$10K approval threshold")
    fig.update_yaxes(tickprefix="$", title="Combined transaction value")
    st.plotly_chart(chart_style(fig, 410), width="stretch")
    st.dataframe(patterns[["pattern_id", "employee_id", "department_name", "vendor_name", "request_ids", "first_date", "last_date", "combined_value", "reason_flagged", "review_status"]], width="stretch", hide_index=True, column_config={"combined_value": st.column_config.NumberColumn("Combined value", format="$%,.0f")})
    st.caption("Method: three or more purchases between 88% and 100% of the $10,000 Finance threshold, for the same employee and vendor, within 21 days, whose combined value exceeds the threshold.")


def system_change_page(data: dict[str, object]) -> None:
    analysis: pd.DataFrame = data["analysis"]
    violations: pd.DataFrame = data["violations"]
    findings = {item["finding_id"]: item for item in data["findings"]}
    page_header("July 1, 2025 / change effectiveness", "System Change Analysis", "Evaluate whether NovaProcure improved control enforcement, where adoption differs, and which unintended consequences appeared after deployment.")
    period = analysis.groupby("system_period", as_index=False).agg(requests=("request_id", "size"), alignment=("aligned", lambda s: s.mean() * 100), drift=("drift_score", "mean"), unusual=("has_unusual_sequence", lambda s: s.mean() * 100), cycle=("cycle_time_hours", "median")).set_index("system_period")
    before, after = period.loc["Before update"], period.loc["After update"]
    cols = st.columns(4)
    changes = [
        ("Alignment", after.alignment - before.alignment, "percentage points"),
        ("Average drift", after.drift - before.drift, "score points"),
        ("Unusual sequences", after.unusual - before.unusual, "percentage points"),
        ("Median cycle", after.cycle - before.cycle, "hours"),
    ]
    for col, (label, delta, unit) in zip(cols, changes):
        with col: metric_card(label, f"{delta:+.1f}", f"After minus before · {unit}")
    c1, c2 = st.columns(2)
    with c1:
        compare = period.reset_index().melt(id_vars="system_period", value_vars=["alignment", "unusual"], var_name="metric", value_name="rate")
        fig = px.bar(compare, x="metric", y="rate", color="system_period", barmode="group", color_discrete_map={"Before update": COLORS["slate"], "After update": COLORS["blue"]}, title="Core control rates before and after")
        fig.update_yaxes(ticksuffix="%", title="Rate")
        fig.update_xaxes(title=None)
        st.plotly_chart(chart_style(fig, 390), width="stretch")
    with c2:
        post = analysis[analysis.system_period == "After update"]
        adoption = post.groupby(["employee_location", "source_system"], as_index=False).size()
        adoption["share"] = adoption["size"] / adoption.groupby("employee_location")["size"].transform("sum") * 100
        fig = px.bar(adoption, x="employee_location", y="share", color="source_system", color_discrete_map={"NovaProcure": COLORS["blue"], "ProcureFlow Classic": COLORS["orange"]}, title="Post-go-live application mix by office")
        fig.update_yaxes(ticksuffix="%", title="Share of requests")
        fig.update_xaxes(title=None)
        st.plotly_chart(chart_style(fig, 390), width="stretch")
    st.markdown('<div class="section-label">Change narrative</div>', unsafe_allow_html=True)
    for finding_id, tone in [("FND-02", "success"), ("FND-03", "warning"), ("FND-04", "warning")]:
        f = findings[finding_id]
        st.markdown(f'<div class="{tone}-strip" style="margin-bottom:10px"><b>{f["title"]}:</b> {f["evidence"]}<br><span style="font-size:.78rem">Hypothesis: {f["root_cause_hypothesis"]}</span></div>', unsafe_allow_html=True)


def simulator_page(data: dict[str, object]) -> None:
    requests: pd.DataFrame = data["requests"]
    page_header("Historical impact simulation / policy design", "Change Impact Simulator", "Change a policy parameter and estimate how the historical request population would have been routed. This is workload estimation, not a prediction of future behavior.")
    st.markdown('<div class="info-strip"><b>Historical Impact Simulation:</b> Results show how past transactions would have been classified under a proposed rule. They do not predict demand or guarantee future outcomes.</div>', unsafe_allow_html=True)
    simulation = st.selectbox("Rule to simulate", ["Finance approval threshold", "Director approval threshold", "Security review scope"])
    if simulation == "Finance approval threshold":
        proposed = st.slider("Proposed Finance threshold", 2_500, 25_000, 5_000, step=500, format="$%d")
        result = simulate_finance_threshold(requests, 10_000, proposed)
    elif simulation == "Director approval threshold":
        proposed = st.slider("Proposed Director threshold", 10_000, 60_000, 40_000, step=1_000, format="$%d")
        result = simulate_director_threshold(requests, 25_000, proposed)
    else:
        c1, c2 = st.columns(2)
        include_ai = c1.toggle("Include AI Services", value=True)
        include_equipment = c2.toggle("Include Equipment", value=False)
        result = simulate_security_scope(requests, include_ai, include_equipment)
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Net review change", f"{result['net_workload_change']:+,}", "Historical transactions")
    with c2: metric_card("Population affected", f"{result['affected_pct']:.1f}%", "Share reclassified")
    with c3: metric_card("Estimated workload", f"{result['estimated_hours']:,.0f}h", "Illustrative analyst handling time")
    with c4: metric_card("Rule state", str(result["proposed"]), f"Current: {result['current']}")
    left, right = st.columns(2)
    with left:
        dept = result["departments"].head(10)
        if not dept.empty:
            fig = px.bar(dept.sort_values("affected_requests"), x="affected_requests", y="department_name", orientation="h", color_discrete_sequence=[COLORS["blue"]], title="Departments most affected")
            fig.update_yaxes(title=None)
            fig.update_xaxes(title="Affected requests")
            st.plotly_chart(chart_style(fig, 410), width="stretch")
    with right:
        category = result["categories"].head(10)
        if not category.empty:
            fig = px.bar(category, x="purchase_type", y="affected_requests", color_discrete_sequence=[COLORS["cyan"]], title="Categories most affected")
            fig.update_xaxes(title=None)
            fig.update_yaxes(title="Affected requests")
            st.plotly_chart(chart_style(fig, 410), width="stretch")
    if abs(result["net_workload_change"]) > len(requests) * 0.1:
        st.markdown('<div class="warning-strip"><b>Capacity flag:</b> The proposed change affects more than 10% of historical requests. Validate reviewer capacity, queue design, and service-level expectations before implementation.</div>', unsafe_allow_html=True)


def recommendations_page(data: dict[str, object]) -> None:
    findings: list[dict] = data["findings"]
    page_header("Evidence to action / requirements linked", "Recommendations", "Each recommendation is tied to a measured finding, a plausible root-cause hypothesis, a system requirement, and a KPI for ongoing governance.")
    st.markdown('<div class="info-strip"><b>Portfolio case study:</b> These are proposed recommendations for a fictional organization. They have not been implemented and no real-world outcome or ROI is claimed.</div>', unsafe_allow_html=True)
    for f in findings:
        st.markdown(
            f'<div class="recommendation"><div class="rec-id">{f["finding_id"]} · {f["requirement"]}</div>'
            f'<div class="rec-title">{f["title"]}</div><div class="rec-grid">'
            f'<div class="rec-item"><b>Evidence</b>{f["evidence"]}</div>'
            f'<div class="rec-item"><b>Root-cause hypothesis</b>{f["root_cause_hypothesis"]}</div>'
            f'<div class="rec-item"><b>Recommendation</b>{f["recommendation"]}</div>'
            f'<div class="rec-item"><b>KPI to monitor</b>{f["kpi"]}</div>'
            f'</div></div>', unsafe_allow_html=True,
        )


def sidebar() -> str:
    with st.sidebar:
        st.markdown('<div class="brand"><div class="brand-mark">TG</div><div><div class="brand-name">TraceGap</div><div class="brand-sub">Process intelligence</div></div></div>', unsafe_allow_html=True)
        selected_label = st.radio("Navigation", [NAV_LABELS[item] for item in NAV_ITEMS], label_visibility="collapsed")
        st.markdown("---")
        st.markdown('<div class="small-muted"><b>Northstar Technologies</b><br>Purchase-to-Pay · FY2025<br>8,500 synthetic requests</div>', unsafe_allow_html=True)
        st.markdown('<div class="small-muted" style="margin-top:18px">Independent portfolio case study.<br>All organizations, people, and transactions are fictional.</div>', unsafe_allow_html=True)
    reverse = {label: key for key, label in NAV_LABELS.items()}
    return reverse[selected_label]


apply_style()
data = load_data()
page = sidebar()

PAGES = {
    "Executive Process Health": executive_page,
    "Process Explorer": process_explorer_page,
    "Rule Compliance": rule_compliance_page,
    "Drift Intelligence": drift_intelligence_page,
    "Transaction Investigator": transaction_investigator_page,
    "Threshold Pattern Detection": threshold_page,
    "System Change Analysis": system_change_page,
    "Change Impact Simulator": simulator_page,
    "Recommendations": recommendations_page,
}
PAGES[page](data)
