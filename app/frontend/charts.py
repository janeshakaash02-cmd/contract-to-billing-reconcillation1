import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, Any, List

THEME_BG = "#070A0F"
THEME_CARD = "#0C121F"
COLOR_NEON_GREEN = "#00FF88"
COLOR_NEON_CYAN = "#00F0FF"
COLOR_NEON_AMBER = "#FFB800"
COLOR_NEON_CRIMSON = "#FF3366"
COLOR_NEON_PURPLE = "#B026FF"
TEXT_COLOR = "#F0F6FC"
GRID_COLOR = "#151F30"

def get_base_layout(title: str = "", height: int = 340) -> Dict[str, Any]:
    """Base Plotly layout settings for dark neon terminal aesthetic."""
    return dict(
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(family="Space Grotesk, sans-serif", size=14, color=TEXT_COLOR),
            x=0.02,
            y=0.96
        ),
        paper_bgcolor=THEME_CARD,
        plot_bgcolor=THEME_CARD,
        font=dict(family="JetBrains Mono, monospace", color="#94A3B8", size=11),
        margin=dict(t=42, b=28, l=32, r=28),
        height=height,
    )

def build_status_donut(metrics: Dict[str, Any]) -> go.Figure:
    """Builds a futuristic dark donut chart of reconciliation classifications."""
    labels = ["Matched", "Probable Match", "Unmatched Exception", "Duplicate", "Data Quality"]
    values = [
        metrics.get('matched', 0),
        metrics.get('probable_matches', 0),
        metrics.get('unmatched', 0),
        metrics.get('duplicates', 0),
        metrics.get('data_quality_exceptions', 0),
    ]
    colors = [COLOR_NEON_GREEN, COLOR_NEON_CYAN, COLOR_NEON_CRIMSON, COLOR_NEON_AMBER, COLOR_NEON_PURPLE]
    
    # Filter non-zero for clean visuals
    filtered_data = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
    if not filtered_data:
        filtered_data = [("None", 1, "#334155")]

    f_labels, f_values, f_colors = zip(*filtered_data)

    fig = go.Figure(data=[go.Pie(
        labels=f_labels,
        values=f_values,
        hole=0.68,
        marker=dict(colors=f_colors, line=dict(color=THEME_BG, width=2)),
        textinfo='percent',
        hoverinfo='label+value+percent',
        textfont=dict(color="#FFFFFF", size=12, family="JetBrains Mono"),
    )])

    # Center label annotation
    match_rate = metrics.get('auto_match_rate', 0.0)
    fig.add_annotation(
        text=f"<b>{match_rate}%</b><br><span style='font-size:10px;color:#8B949E;'>AUTO-RATE</span>",
        x=0.5, y=0.5,
        font=dict(family="Space Grotesk, sans-serif", size=18, color=COLOR_NEON_GREEN),
        showarrow=False
    )

    layout = get_base_layout("Reconciliation Classification", height=320)
    layout["showlegend"] = True
    layout["legend"] = dict(
        orientation="h",
        yanchor="top",
        y=-0.08,
        xanchor="center",
        x=0.5,
        font=dict(size=10)
    )
    fig.update_layout(layout)
    return fig

def build_exposure_bar(metrics: Dict[str, Any]) -> go.Figure:
    """Horizontal bar chart showing top exception categories ranked by financial exposure."""
    top_reasons = metrics.get('top_reasons', [])
    if not top_reasons:
        fig = go.Figure()
        fig.update_layout(get_base_layout("Top Exception Categories", height=320))
        fig.add_annotation(text="No active exceptions recorded", x=0.5, y=0.5, showarrow=False, font=dict(color="#64748B"))
        return fig

    df = pd.DataFrame(top_reasons)
    df["short_label"] = df["reason"].apply(lambda x: x[:34] + "..." if len(x) > 34 else x)

    fig = go.Figure(go.Bar(
        x=df["exposure"],
        y=df["short_label"],
        orientation='h',
        marker=dict(
            color=df["exposure"],
            colorscale=[[0, "#FF6B8B"], [0.5, "#FF3366"], [1, "#FF0040"]],
            line=dict(color="rgba(255,51,102,0.4)", width=1)
        ),
        text=df["exposure"].apply(lambda v: f"${v:,.0f}"),
        textposition="outside",
        textfont=dict(color=TEXT_COLOR, size=10, family="JetBrains Mono"),
        hovertemplate="<b>%{y}</b><br>Exposure: $%{x:,.2f}<extra></extra>"
    ))

    layout = get_base_layout("Financial Exposure by Exception Root Cause", height=320)
    layout["xaxis"] = dict(
        title="At-Risk Exposure ($)",
        gridcolor=GRID_COLOR,
        color="#8B949E",
        tickprefix="$",
        showgrid=True
    )
    layout["yaxis"] = dict(
        autorange="reversed",
        color="#CBD5E1",
        gridcolor=GRID_COLOR
    )
    fig.update_layout(layout)
    return fig

def build_neon_sankey(metrics: Dict[str, Any], results: List[Any]) -> go.Figure:
    """
    Creates an interactive Neon Sankey diagram visualizing the journey of billing records:
    Total Ingested -> Matching Strategy Tier -> Classification -> Financial Resolution
    """
    total_invoices = metrics.get('total_reconciled', len(results))
    matched_count = metrics.get('matched', 0)
    probable_count = metrics.get('probable_matches', 0)
    unmatched_count = metrics.get('unmatched', 0)
    dq_count = metrics.get('data_quality_exceptions', 0)
    dup_count = metrics.get('duplicates', 0)

    # Estimate strategy breakdown
    exact_count = max(0, matched_count - 5)
    tolerance_count = max(0, matched_count - exact_count + probable_count)
    fuzzy_count = max(0, total_invoices - exact_count - tolerance_count)

    # Node definitions
    node_labels = [
        f"Ingested Invoices ({total_invoices})",  # 0
        f"Exact Key Tier ({exact_count})",        # 1
        f"Tolerance Matcher ({tolerance_count})", # 2
        f"Fuzzy/Policy Engine ({fuzzy_count})",   # 3
        f"Auto-Matched ({matched_count})",        # 4
        f"Probable Matches ({probable_count})",   # 5
        f"Billing Exceptions ({unmatched_count})",# 6
        f"Data Quality / Dupes ({dq_count + dup_count})", # 7
        f"Clean Clearance (${metrics.get('cost_saved', 0)*20:,.0f})", # 8
        f"Financial Exposure (${metrics.get('total_financial_exposure', 0):,.0f})", # 9
    ]

    node_colors = [
        "#38BDF8",            # 0 Influx
        COLOR_NEON_GREEN,     # 1 Exact
        COLOR_NEON_CYAN,      # 2 Tolerance
        COLOR_NEON_AMBER,     # 3 Fuzzy
        COLOR_NEON_GREEN,     # 4 Matched
        COLOR_NEON_CYAN,      # 5 Probable
        COLOR_NEON_CRIMSON,   # 6 Exceptions
        COLOR_NEON_PURPLE,    # 7 DQ
        COLOR_NEON_GREEN,     # 8 Clearance
        COLOR_NEON_CRIMSON,   # 9 Exposure
    ]

    # Links: source, target, value, color
    links = [
        # Ingestion to Tiers
        {"source": 0, "target": 1, "value": max(1, exact_count), "color": "rgba(0, 255, 136, 0.25)"},
        {"source": 0, "target": 2, "value": max(1, tolerance_count), "color": "rgba(0, 240, 255, 0.25)"},
        {"source": 0, "target": 3, "value": max(1, fuzzy_count), "color": "rgba(255, 184, 0, 0.25)"},
        
        # Tiers to Statuses
        {"source": 1, "target": 4, "value": max(1, exact_count), "color": "rgba(0, 255, 136, 0.35)"},
        {"source": 2, "target": 4, "value": max(1, max(0, matched_count - exact_count)), "color": "rgba(0, 255, 136, 0.3)"},
        {"source": 2, "target": 5, "value": max(1, probable_count), "color": "rgba(0, 240, 255, 0.35)"},
        {"source": 3, "target": 6, "value": max(1, unmatched_count), "color": "rgba(255, 51, 102, 0.35)"},
        {"source": 3, "target": 7, "value": max(1, dq_count + dup_count), "color": "rgba(176, 38, 255, 0.35)"},

        # Statuses to Final Financial Resolution
        {"source": 4, "target": 8, "value": max(1, matched_count), "color": "rgba(0, 255, 136, 0.4)"},
        {"source": 5, "target": 8, "value": max(1, probable_count), "color": "rgba(0, 240, 255, 0.3)"},
        {"source": 6, "target": 9, "value": max(1, unmatched_count), "color": "rgba(255, 51, 102, 0.45)"},
        {"source": 7, "target": 9, "value": max(1, dq_count + dup_count), "color": "rgba(255, 51, 102, 0.35)"},
    ]

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=18,
            thickness=16,
            line=dict(color=THEME_BG, width=1.5),
            label=node_labels,
            color=node_colors
        ),
        link=dict(
            source=[l["source"] for l in links],
            target=[l["target"] for l in links],
            value=[l["value"] for l in links],
            color=[l["color"] for l in links]
        )
    )])

    layout = get_base_layout("Reconciliation Pipeline Flow (Ingestion ➔ Strategy ➔ Risk Outcome)", height=380)
    fig.update_layout(layout)
    return fig

def build_confidence_gauge(confidence_score: float) -> go.Figure:
    """Builds a high-tech semi-circular neon confidence meter (0 to 100%)."""
    score_pct = int(confidence_score * 100)
    color = COLOR_NEON_GREEN if score_pct >= 85 else (COLOR_NEON_CYAN if score_pct >= 65 else COLOR_NEON_CRIMSON)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score_pct,
        number=dict(suffix="%", font=dict(color=color, size=32, family="Space Grotesk")),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#4B5563", tickfont=dict(color="#8B949E", size=10)),
            bar=dict(color=color, thickness=0.3),
            bgcolor=THEME_CARD,
            borderwidth=1,
            bordercolor="#1E293B",
            steps=[
                dict(range=[0, 60], color="rgba(255, 51, 102, 0.15)"),
                dict(range=[60, 85], color="rgba(0, 240, 255, 0.15)"),
                dict(range=[85, 100], color="rgba(0, 255, 136, 0.15)"),
            ],
            threshold=dict(
                line=dict(color="#FFFFFF", width=2),
                thickness=0.75,
                value=85
            )
        )
    ))

    layout = get_base_layout("Deterministic Confidence Score", height=240)
    layout["margin"] = dict(t=35, b=20, l=30, r=30)
    fig.update_layout(layout)
    return fig

def build_tolerance_meter(variance_percent: float, tolerance_percent: float) -> go.Figure:
    """Visualizes how much of allowable contractual tolerance was consumed."""
    ratio = (variance_percent / max(0.001, tolerance_percent)) * 100
    color = COLOR_NEON_GREEN if variance_percent <= tolerance_percent else COLOR_NEON_CRIMSON

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=min(200.0, ratio),
        number=dict(suffix="%", font=dict(color=color, size=28, family="Space Grotesk")),
        title=dict(
            text=f"Variance: {variance_percent:.2f}% | Max Limit: {tolerance_percent:.2f}%",
            font=dict(color="#94A3B8", size=11, family="JetBrains Mono")
        ),
        gauge=dict(
            axis=dict(range=[0, 150], tickcolor="#4B5563", tickfont=dict(color="#8B949E", size=9)),
            bar=dict(color=color, thickness=0.3),
            bgcolor=THEME_CARD,
            borderwidth=1,
            bordercolor="#1E293B",
            steps=[
                dict(range=[0, 100], color="rgba(0, 255, 136, 0.15)"),
                dict(range=[100, 150], color="rgba(255, 51, 102, 0.25)"),
            ],
            threshold=dict(
                line=dict(color=COLOR_NEON_CRIMSON, width=3),
                thickness=0.8,
                value=100
            )
        )
    ))

    layout = get_base_layout("Contract Tolerance Consumption", height=220)
    layout["margin"] = dict(t=35, b=20, l=30, r=30)
    fig.update_layout(layout)
    return fig

def build_roi_payback_chart(
    monthly_invoices: int,
    manual_minutes: int,
    hourly_rate: float,
    auto_match_rate: float
) -> go.Figure:
    """Generates a 12-month cumulative financial labor savings projection."""
    months = [f"M{i}" for i in range(1, 13)]
    monthly_manual_cost = (monthly_invoices * (manual_minutes / 60.0)) * hourly_rate
    monthly_saved = monthly_manual_cost * (auto_match_rate / 100.0)
    
    cumulative_manual = [monthly_manual_cost * i for i in range(1, 13)]
    cumulative_savings = [monthly_saved * i for i in range(1, 13)]
    cumulative_residual = [cum_man - cum_sav for cum_man, cum_sav in zip(cumulative_manual, cumulative_savings)]

    fig = go.Figure()

    # Manual Baseline
    fig.add_trace(go.Scatter(
        x=months,
        y=cumulative_manual,
        mode='lines+markers',
        name='Manual Baseline Cost',
        line=dict(color="#FF3366", width=2, dash='dash'),
        marker=dict(size=5)
    ))

    # Automated Cost Savings
    fig.add_trace(go.Scatter(
        x=months,
        y=cumulative_savings,
        mode='lines+markers',
        name='Cumulative Cost Savings',
        fill='tozeroy',
        fillcolor='rgba(0, 255, 136, 0.12)',
        line=dict(color=COLOR_NEON_GREEN, width=3),
        marker=dict(size=6, color=COLOR_NEON_GREEN)
    ))

    # Residual Labor Cost
    fig.add_trace(go.Scatter(
        x=months,
        y=cumulative_residual,
        mode='lines',
        name='Residual Exception Audit Cost',
        line=dict(color="#00F0FF", width=2),
    ))

    layout = get_base_layout("12-Month Cumulative Financial Savings Projection", height=340)
    layout["xaxis"] = dict(gridcolor=GRID_COLOR, color="#8B949E")
    layout["yaxis"] = dict(gridcolor=GRID_COLOR, color="#8B949E", tickprefix="$")
    layout["showlegend"] = True
    layout["legend"] = dict(
        orientation="h",
        yanchor="top",
        y=-0.12,
        xanchor="center",
        x=0.5,
        font=dict(size=10)
    )
    fig.update_layout(layout)
    return fig
