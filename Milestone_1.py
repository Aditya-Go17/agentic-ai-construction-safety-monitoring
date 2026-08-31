import json
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output


# ============================================================
# APP CONFIGURATION
# ============================================================

app = Dash(
    __name__,
    title="BuildSure AI | Site Risk Dashboard"
)

server = app.server


# ============================================================
# CONSTANTS
# ============================================================

ZONES = [
    "Foundation Area",
    "Scaffolding Zone A",
    "Crane Operation Zone",
    "Electrical Panel Room",
    "Material Storage Yard",
    "Excavation Pit",
    "Rooftop Work Area",
    "Main Site Entrance",
]

ZONE_COORDS = {
    "Foundation Area": (1, 1),
    "Scaffolding Zone A": (3, 1),
    "Crane Operation Zone": (5, 1),
    "Electrical Panel Room": (1, 3),
    "Material Storage Yard": (3, 3),
    "Excavation Pit": (5, 3),
    "Rooftop Work Area": (2, 5),
    "Main Site Entrance": (4, 5),
}

RISK_TYPES = [
    "Fall Hazards",
    "Equipment Risks",
    "Electrical Hazards",
    "Environmental Risks",
    "Structural Risks",
]

STATUSES = [
    "Open",
    "Under Review",
    "Mitigated",
]

EQUIPMENT = [
    "Tower Crane",
    "Excavator",
    "Scaffolding System",
    "Forklift",
    "Concrete Mixer",
    "Diesel Generator",
    "Bulldozer",
    "Welding Unit",
]

DESCRIPTIONS = {
    "Fall Hazards": [
        "Missing guardrail near open edge",
        "Worker without harness at height",
        "Unstable scaffolding platform",
        "Unprotected floor opening",
    ],
    "Equipment Risks": [
        "Crane load exceeding rated capacity",
        "Excavator hydraulic leak detected",
        "Forklift operating in blind zone",
        "Unsecured heavy machinery",
    ],
    "Electrical Hazards": [
        "Exposed live wiring",
        "Overloaded temporary power board",
        "Damaged cable insulation",
        "Missing lockout-tagout tag",
    ],
    "Environmental Risks": [
        "High dust concentration detected",
        "Excessive noise levels",
        "Poor site drainage / flooding risk",
        "Extreme heat exposure",
    ],
    "Structural Risks": [
        "Formwork instability observed",
        "Cracks in temporary support",
        "Overloaded storage racking",
        "Uneven ground settlement",
    ],
}

RISK_TYPE_COLORS = {
    "Fall Hazards": "#ef4444",
    "Equipment Risks": "#f97316",
    "Electrical Hazards": "#3b82f6",
    "Environmental Risks": "#8b5cf6",
    "Structural Risks": "#14b8a6",
}


# ============================================================
# DATA GENERATION
# ============================================================

def get_severity_label(score):
    if score <= 6:
        return "Low"
    elif score <= 9:
        return "Medium"
    elif score <= 12:
        return "Medium-High"
    elif score <= 16:
        return "High"
    return "Critical"


def generate_data(seed=42, n_records=260):
    """
    Simulated Site Risk Agent data.

    This represents information received from:
    - CCTV monitoring
    - Site inspection reports
    - Equipment sensors
    - Environmental sensors
    """

    rng = np.random.default_rng(seed)
    now = pd.Timestamp.now().floor("min")

    # --------------------------------------------------------
    # Hazard records
    # --------------------------------------------------------

    risk_types = rng.choice(
        RISK_TYPES,
        n_records,
        p=[0.30, 0.24, 0.18, 0.16, 0.12]
    )

    risk_df = pd.DataFrame({
        "risk_id": [
            f"RSK-{i:04d}"
            for i in range(1, n_records + 1)
        ],
        "zone": rng.choice(ZONES, n_records),
        "risk_type": risk_types,
        "probability": rng.choice(
            [1, 2, 3, 4, 5],
            n_records,
            p=[0.10, 0.30, 0.30, 0.22, 0.08]
        ),
        "impact": rng.choice(
            [1, 2, 3, 4, 5],
            n_records,
            p=[0.08, 0.27, 0.32, 0.23, 0.10]
        ),
        "status": rng.choice(
            STATUSES,
            n_records,
            p=[0.42, 0.20, 0.38]
        ),
        "detected_at": now - pd.to_timedelta(
            rng.uniform(0, 24 * 30, n_records),
            unit="h"
        ),
    })

    risk_df["description"] = [
        rng.choice(DESCRIPTIONS[risk_type])
        for risk_type in risk_df["risk_type"]
    ]

    risk_df["severity_score"] = (
        risk_df["probability"] * risk_df["impact"]
    ).astype(int)

    risk_df["severity_label"] = risk_df[
        "severity_score"
    ].apply(get_severity_label)

    # --------------------------------------------------------
    # Equipment monitoring
    # --------------------------------------------------------

    equipment_count = len(EQUIPMENT) * 3

    equipment_df = pd.DataFrame({
        "equipment_id": [
            f"EQ-{i:03d}"
            for i in range(1, equipment_count + 1)
        ],
        "equipment_name": np.tile(EQUIPMENT, 3),
        "zone": rng.choice(ZONES, equipment_count),
        "risk_score": rng.integers(
            35,
            98,
            equipment_count
        ),
        "last_inspection_days_ago": rng.integers(
            0,
            45,
            equipment_count
        ),
    })

    equipment_df["status"] = np.select(
        [
            equipment_df["risk_score"] >= 80,
            equipment_df["risk_score"] >= 60,
        ],
        [
            "Critical",
            "Needs Inspection",
        ],
        default="Operational"
    )

    # --------------------------------------------------------
    # Environmental monitoring
    # --------------------------------------------------------

    environment_df = pd.DataFrame({
        "zone": ZONES,
        "temperature_c": rng.uniform(
            24,
            39,
            len(ZONES)
        ).round(1),
        "humidity_pct": rng.uniform(
            35,
            88,
            len(ZONES)
        ).round(1),
        "aqi": rng.integers(
            25,
            180,
            len(ZONES)
        ),
        "noise_db": rng.integers(
            58,
            108,
            len(ZONES)
        ),
        "dust_index": rng.integers(
            10,
            95,
            len(ZONES)
        ),
    })

    environment_df["env_risk_score"] = (
        (environment_df["aqi"] / 180) * 35
        + (environment_df["noise_db"] / 108) * 30
        + (environment_df["dust_index"] / 95) * 35
    ).round(1)

    # --------------------------------------------------------
    # Daily activity data
    # --------------------------------------------------------

    dates = pd.date_range(
        now.normalize() - pd.Timedelta(days=29),
        now.normalize(),
        freq="D"
    )

    daily_hazards = (
        risk_df["detected_at"]
        .dt.normalize()
        .value_counts()
        .reindex(dates, fill_value=0)
        .astype(int)
        .values
    )

    activity_df = pd.DataFrame({
        "date": dates,
        "workers_onsite": rng.integers(
            180,
            360,
            len(dates)
        ),
        "equipment_active": rng.integers(
            15,
            45,
            len(dates)
        ),
        "hazards_detected": daily_hazards,
        "incidents_logged": rng.integers(
            0,
            4,
            len(dates)
        ),
    })

    return risk_df, equipment_df, environment_df, activity_df


# ============================================================
# FIGURE HELPERS
# ============================================================

def empty_figure(message="No data available"):
    figure = go.Figure()

    figure.update_layout(
        height=340,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {
                    "size": 16,
                    "color": "#64748b",
                },
            }
        ],
    )

    return figure


def format_figure(figure, height=340):
    figure.update_layout(
        height=height,
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={
            "family": "Arial",
            "color": "#334155",
        },
        margin={
            "l": 20,
            "r": 20,
            "t": 20,
            "b": 30,
        },
        legend={
            "orientation": "h",
            "y": 1.08,
            "x": 0,
        },
    )

    return figure


def build_heatmap(data):
    rows = [5, 4, 3, 2, 1]
    columns = [1, 2, 3, 4, 5]

    if data.empty:
        matrix = pd.DataFrame(
            0,
            index=rows,
            columns=columns
        )
    else:
        matrix = pd.crosstab(
            data["probability"],
            data["impact"]
        ).reindex(
            index=rows,
            columns=columns,
            fill_value=0
        )

    figure = go.Figure(
        go.Heatmap(
            z=matrix.values,
            x=[
                "Negligible",
                "Minor",
                "Moderate",
                "Major",
                "Catastrophic",
            ],
            y=[
                "Almost Certain",
                "Likely",
                "Possible",
                "Unlikely",
                "Rare",
            ],
            text=matrix.values,
            texttemplate="%{text}",
            showscale=False,
            colorscale=[
                [0.00, "#22c55e"],
                [0.35, "#eab308"],
                [0.60, "#f97316"],
                [1.00, "#ef4444"],
            ],
            hovertemplate=(
                "Impact: %{x}<br>"
                "Probability: %{y}<br>"
                "Hazards: %{z}<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        height=350,
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={
            "l": 90,
            "r": 20,
            "t": 15,
            "b": 70,
        },
        xaxis_title="Impact",
        yaxis_title="Probability",
    )

    return figure


def build_risk_distribution(data):
    if data.empty:
        return empty_figure("No hazards match the selected filters")

    chart_df = (
        data["risk_type"]
        .value_counts()
        .rename_axis("risk_type")
        .reset_index(name="count")
    )

    figure = px.bar(
        chart_df,
        x="count",
        y="risk_type",
        orientation="h",
        text="count",
        color="risk_type",
        color_discrete_map=RISK_TYPE_COLORS,
    )

    figure.update_traces(
        textposition="outside"
    )

    figure.update_layout(
        xaxis_title="Hazard Count",
        yaxis_title="",
        showlegend=False,
    )

    return format_figure(figure)


def build_status_chart(data):
    if data.empty:
        return empty_figure("No status data available")

    chart_df = (
        data["status"]
        .value_counts()
        .rename_axis("status")
        .reset_index(name="count")
    )

    figure = px.pie(
        chart_df,
        names="status",
        values="count",
        hole=0.60,
        color="status",
        color_discrete_map={
            "Open": "#ef4444",
            "Under Review": "#f59e0b",
            "Mitigated": "#22c55e",
        },
    )

    figure.update_layout(
        showlegend=True,
        legend={
            "orientation": "h",
            "y": -0.05,
        },
    )

    return format_figure(figure)


def build_zone_summary(data):
    summary = (
        data
        .groupby("zone")
        .agg(
            hazards=("risk_id", "count"),
            avg_severity=("severity_score", "mean")
        )
        .reindex(ZONES)
        .fillna(0)
    )

    summary["hazards"] = summary["hazards"].astype(int)
    summary["avg_severity"] = summary[
        "avg_severity"
    ].round(1)

    summary["risk_level"] = summary[
        "avg_severity"
    ].apply(get_severity_label)

    summary["x"] = [
        ZONE_COORDS[zone][0]
        for zone in summary.index
    ]

    summary["y"] = [
        ZONE_COORDS[zone][1]
        for zone in summary.index
    ]

    summary["marker_size"] = (
        summary["hazards"] * 6 + 10
    )

    return summary.reset_index()


def build_site_map(data):
    if data.empty:
        return empty_figure("No site map data available")

    figure = px.scatter(
        data,
        x="x",
        y="y",
        size="marker_size",
        color="avg_severity",
        text="zone",
        size_max=60,
        range_color=[0, 25],
        color_continuous_scale=[
            "#22c55e",
            "#eab308",
            "#f97316",
            "#ef4444",
        ],
        hover_data={
            "zone": True,
            "hazards": True,
            "avg_severity": ":.1f",
            "risk_level": True,
            "x": False,
            "y": False,
            "marker_size": False,
        },
    )

    figure.update_traces(
        textposition="bottom center",
        marker={
            "line": {
                "width": 2,
                "color": "white",
            }
        },
    )

    figure.update_xaxes(
        visible=False,
        range=[0, 6]
    )

    figure.update_yaxes(
        visible=False,
        range=[0, 6]
    )

    figure.update_layout(
        height=480,
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        font={
            "color": "#e2e8f0"
        },
        margin={
            "l": 20,
            "r": 20,
            "t": 25,
            "b": 20,
        },
        coloraxis_colorbar={
            "title": "Severity"
        },
    )

    return figure


def build_hazard_trend(data, lookback):
    end_date = pd.Timestamp.now().normalize()
    start_date = (
        end_date - pd.Timedelta(days=lookback - 1)
    )

    dates = pd.date_range(
        start_date,
        end_date,
        freq="D"
    )

    if data.empty:
        counts = pd.Series(
            0,
            index=dates
        )
    else:
        counts = (
            data["detected_at"]
            .dt.normalize()
            .value_counts()
            .reindex(
                dates,
                fill_value=0
            )
            .sort_index()
        )

    trend_df = pd.DataFrame({
        "date": dates,
        "hazards_detected": counts.values,
    })

    figure = px.area(
        trend_df,
        x="date",
        y="hazards_detected",
        color_discrete_sequence=["#ef4444"],
    )

    figure.update_traces(
        line={
            "width": 3,
            "color": "#ef4444",
        },
        fillcolor="rgba(239,68,68,0.18)",
    )

    figure.update_layout(
        xaxis_title="",
        yaxis_title="Hazards Detected",
    )

    return format_figure(figure, 310)


def build_equipment_chart(data):
    if data.empty:
        return empty_figure("No equipment data available")

    chart_df = data.sort_values(
        "risk_score",
        ascending=True
    )

    figure = px.bar(
        chart_df,
        x="risk_score",
        y="equipment_name",
        orientation="h",
        color="status",
        color_discrete_map={
            "Critical": "#ef4444",
            "Needs Inspection": "#f59e0b",
            "Operational": "#22c55e",
        },
        hover_data=[
            "equipment_id",
            "zone",
            "last_inspection_days_ago",
        ],
    )

    figure.update_layout(
        xaxis_title="Equipment Risk Score",
        yaxis_title="",
        xaxis_range=[0, 100],
    )

    return format_figure(figure, 440)


def build_environment_chart(data):
    if data.empty:
        return empty_figure("No environmental data available")

    chart_df = data.sort_values(
        "env_risk_score",
        ascending=False
    )

    figure = px.bar(
        chart_df,
        x="zone",
        y="env_risk_score",
        color="env_risk_score",
        range_color=[0, 100],
        color_continuous_scale=[
            "#22c55e",
            "#eab308",
            "#ef4444",
        ],
    )

    figure.update_layout(
        xaxis_title="",
        yaxis_title="Environmental Risk Score",
    )

    return format_figure(figure, 360)


def build_environment_gauge(data):
    value = 0

    if not data.empty:
        value = float(
            data["env_risk_score"].mean()
        )

    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={
                "suffix": "/100",
                "font": {
                    "size": 34
                },
            },
            title={
                "text": "Average Environmental Risk",
                "font": {
                    "size": 16
                },
            },
            gauge={
                "axis": {
                    "range": [0, 100]
                },
                "bar": {
                    "color": "#0f172a"
                },
                "steps": [
                    {
                        "range": [0, 40],
                        "color": "#bbf7d0"
                    },
                    {
                        "range": [40, 70],
                        "color": "#fde68a"
                    },
                    {
                        "range": [70, 100],
                        "color": "#fecaca"
                    },
                ],
            },
        )
    )

    figure.update_layout(
        height=360,
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        margin={
            "l": 25,
            "r": 25,
            "t": 45,
            "b": 15,
        },
    )

    return figure


def build_activity_chart(activity_df, risk_df, lookback):
    end_date = pd.Timestamp.now().normalize()

    start_date = (
        end_date - pd.Timedelta(days=lookback - 1)
    )

    activity_view = activity_df[
        activity_df["date"] >= start_date
    ].copy()

    if risk_df.empty:
        hazard_counts = pd.Series(
            0,
            index=activity_view["date"]
        )
    else:
        hazard_counts = (
            risk_df["detected_at"]
            .dt.normalize()
            .value_counts()
            .reindex(
                activity_view["date"],
                fill_value=0
            )
        )

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=activity_view["date"],
            y=activity_view["workers_onsite"],
            name="Workers Onsite",
            mode="lines+markers",
            line={
                "color": "#3b82f6",
                "width": 3,
            },
        )
    )

    figure.add_trace(
        go.Scatter(
            x=activity_view["date"],
            y=activity_view["equipment_active"],
            name="Active Equipment",
            mode="lines",
            line={
                "color": "#8b5cf6",
                "width": 2,
                "dash": "dot",
            },
        )
    )

    figure.add_trace(
        go.Scatter(
            x=activity_view["date"],
            y=hazard_counts.values * 10,
            name="Hazards Detected ×10",
            mode="lines+markers",
            line={
                "color": "#ef4444",
                "width": 3,
            },
        )
    )

    figure.update_layout(
        xaxis_title="",
        yaxis_title="Activity Level",
    )

    return format_figure(figure, 360)


# ============================================================
# UI COMPONENTS
# ============================================================

def create_kpi(icon, title, value, subtitle, color):
    return html.Div(
        [
            html.Div(
                icon,
                className="kpi-icon"
            ),
            html.Div(
                title,
                className="kpi-title"
            ),
            html.Div(
                value,
                className="kpi-value"
            ),
            html.Div(
                subtitle,
                className="kpi-subtitle"
            ),
        ],
        className="kpi-card",
        style={
            "borderLeft": f"5px solid {color}"
        }
    )


def section_heading(title, subtitle=None):
    children = [
        html.H2(title)
    ]

    if subtitle:
        children.append(
            html.P(subtitle)
        )

    return html.Div(
        children,
        className="section-heading"
    )


def recommendation(priority, title, description):
    return html.Div(
        [
            html.Span(
                priority.upper(),
                className=f"priority-pill {priority}"
            ),
            html.Div(
                f"💡 {title}",
                className="recommendation-title"
            ),
            html.Div(
                description,
                className="recommendation-description"
            ),
        ],
        className=f"recommendation-card {priority}"
    )


def create_recommendations(
    risk_df,
    equipment_df,
    environment_df
):
    if risk_df.empty:
        return html.Div(
            [
                html.Div(
                    "No recommendations available",
                    className="empty-title"
                ),
                html.Div(
                    "Adjust the selected filters to view recommendations.",
                    className="empty-description"
                ),
            ],
            className="empty-state"
        )

    cards = []

    top_type = risk_df[
        "risk_type"
    ].value_counts().idxmax()

    top_zone = (
        risk_df[
            risk_df["risk_type"] == top_type
        ]["zone"]
        .value_counts()
        .idxmax()
    )

    cards.append(
        recommendation(
            "high",
            f"Investigate {top_type} in {top_zone}",
            f"{top_type} is the most frequently detected hazard category. "
            f"Conduct an immediate inspection and assign corrective action "
            f"to the supervisor responsible for {top_zone}.",
        )
    )

    zone_scores = risk_df.groupby(
        "zone"
    )["severity_score"].mean()

    if not zone_scores.empty:
        worst_zone = zone_scores.idxmax()
        worst_score = zone_scores.max()

        cards.append(
            recommendation(
                "high",
                f"Escalate monitoring for {worst_zone}",
                f"This zone has the highest average severity score of "
                f"{worst_score:.1f}/25. Increase supervisor walkthroughs "
                f"and verify the latest inspection evidence.",
            )
        )

    critical_equipment = equipment_df[
        equipment_df["status"] == "Critical"
    ]

    if not critical_equipment.empty:
        equipment_name = critical_equipment.iloc[0][
            "equipment_name"
        ]

        cards.append(
            recommendation(
                "medium",
                f"Inspect {equipment_name}",
                f"{len(critical_equipment)} equipment unit(s) "
                f"are classified as critical. Schedule maintenance "
                f"before the next work shift.",
            )
        )

    if not environment_df.empty:
        worst_environment = environment_df.sort_values(
            "env_risk_score",
            ascending=False
        ).iloc[0]

        cards.append(
            recommendation(
                "medium",
                f"Review conditions in {worst_environment['zone']}",
                f"The environmental risk score is "
                f"{worst_environment['env_risk_score']:.1f}/100. "
                f"Review dust, noise, air quality and heat controls.",
            )
        )

    open_hazards = int(
        (risk_df["status"] == "Open").sum()
    )

    if open_hazards > 0:
        cards.append(
            recommendation(
                "low",
                "Close open hazard tickets",
                f"{open_hazards} hazard records are currently open. "
                f"Assign owners and define resolution deadlines.",
            )
        )

    return cards


def records_as_json(dataframe):
    """
    Converts pandas records into JSON-compatible Python records.
    """
    return json.loads(
        dataframe.to_json(
            orient="records"
        )
    )


# ============================================================
# INLINE CSS
# ============================================================

app.index_string = """
<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>BuildSure AI</title>
    {%favicon%}
    {%css%}

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            background: #f4f7fb;
            color: #0f172a;
            font-family: Arial, sans-serif;
        }

        .app-shell {
            display: flex;
            min-height: 100vh;
        }

        /* Sidebar */

        .sidebar {
            width: 285px;
            min-height: 100vh;
            padding: 25px 20px;
            background:
                radial-gradient(
                    circle at 20% 0%,
                    #263b5d 0%,
                    transparent 30%
                ),
                linear-gradient(
                    180deg,
                    #0f172a 0%,
                    #111c30 100%
                );
            color: #e2e8f0;
            position: sticky;
            top: 0;
            height: 100vh;
            overflow-y: auto;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 23px;
        }

        .brand-symbol {
            width: 43px;
            height: 43px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 12px;
            background: linear-gradient(
                135deg,
                #f97316,
                #fb923c
            );
            color: white;
            font-weight: 900;
            font-size: 18px;
        }

        .brand-name {
            color: white;
            font-size: 21px;
            font-weight: 800;
        }

        .brand-subtitle {
            margin-top: 3px;
            color: #94a3b8;
            font-size: 9px;
            letter-spacing: 1.5px;
        }

        .milestone-label {
            display: inline-block;
            padding: 6px 10px;
            border: 1px solid rgba(249, 115, 22, 0.5);
            border-radius: 20px;
            color: #fb923c;
            background: rgba(249, 115, 22, 0.14);
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 1px;
        }

        .sidebar-description {
            color: #cbd5e1;
            font-size: 13px;
            line-height: 1.5;
            margin: 13px 0 20px;
        }

        .sidebar-divider {
            height: 1px;
            background: rgba(148, 163, 184, 0.18);
            margin: 20px 0;
        }

        .filter-heading,
        .feed-heading {
            color: #94a3b8;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 1.4px;
            margin-bottom: 12px;
        }

        .filter-label {
            display: block;
            color: #cbd5e1;
            font-size: 12px;
            font-weight: 600;
            margin: 15px 0 7px;
        }

        .sidebar .Select-control {
            background: #17263d !important;
            border: 1px solid #334155 !important;
            border-radius: 8px !important;
        }

        .sidebar .Select-placeholder,
        .sidebar .Select-value-label {
            color: #e2e8f0 !important;
            font-size: 12px;
        }

        .sidebar .Select-menu-outer {
            background: #17263d !important;
            color: white !important;
            border: 1px solid #334155 !important;
            z-index: 9999;
        }

        .sidebar .Select-option {
            background: #17263d !important;
            color: #e2e8f0 !important;
            font-size: 12px;
        }

        .sidebar .Select-option.is-focused {
            background: #263b5d !important;
        }

        .sidebar .Select--multi .Select-value {
            background: #263b5d !important;
            border: 1px solid #475569 !important;
            color: white !important;
        }

        .sidebar .Select--multi .Select-value-label,
        .sidebar .Select--multi .Select-value-icon {
            color: white !important;
        }

        .sidebar .rc-slider-mark-text {
            color: #94a3b8 !important;
            font-size: 10px;
        }

        .sidebar-slider {
            margin: 28px 10px 36px;
        }

        .refresh-button {
            width: 100%;
            padding: 12px 15px;
            border: none;
            border-radius: 9px;
            background: linear-gradient(
                135deg,
                #f97316,
                #ea580c
            );
            color: white;
            font-size: 13px;
            font-weight: 800;
            cursor: pointer;
        }

        .refresh-button:hover {
            background: linear-gradient(
                135deg,
                #fb923c,
                #f97316
            );
        }

        .feed-card {
            margin-top: 28px;
            padding: 15px;
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 11px;
            background: rgba(255, 255, 255, 0.04);
        }

        .feed-item {
            padding: 5px 0;
            color: #cbd5e1;
            font-size: 12px;
        }

        .sidebar-footer {
            margin-top: 25px;
            color: #64748b;
            font-size: 11px;
            line-height: 1.5;
        }

        /* Main content */

        .main-content {
            flex: 1;
            max-width: 1700px;
            margin: 0 auto;
            padding: 27px 34px;
        }

        .topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 22px;
        }

        .topbar-eyebrow {
            color: #f97316;
            font-size: 10px;
            font-weight: 900;
            letter-spacing: 1.5px;
        }

        .topbar-title {
            margin-top: 4px;
            color: #0f172a;
            font-size: 22px;
            font-weight: 800;
        }

        .topbar-status {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .live-pill {
            display: inline-block;
            padding: 7px 12px;
            border-radius: 20px;
            background: #fee2e2;
            color: #dc2626;
            font-size: 11px;
            font-weight: 800;
        }

        .sync-time {
            color: #64748b;
            font-size: 11px;
        }

        /* Hero */

        .hero {
            min-height: 205px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 32px 38px;
            margin-bottom: 22px;
            border-radius: 20px;
            overflow: hidden;
            color: white;
            background:
                radial-gradient(
                    circle at 75% 30%,
                    rgba(59, 130, 246, 0.32),
                    transparent 30%
                ),
                radial-gradient(
                    circle at 95% 100%,
                    rgba(249, 115, 22, 0.2),
                    transparent 25%
                ),
                linear-gradient(
                    120deg,
                    #0b1425 0%,
                    #17263d 65%,
                    #0f172a 100%
                );
            box-shadow: 0 18px 35px rgba(15, 23, 42, 0.2);
        }

        .hero-label {
            color: #93c5fd;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 1.4px;
        }

        .hero-tag {
            margin-left: 7px;
            color: #fb923c;
        }

        .hero h1 {
            max-width: 680px;
            margin: 14px 0 12px;
            font-size: 36px;
            line-height: 1.1;
        }

        .hero-highlight {
            color: #fb923c;
        }

        .hero-description {
            max-width: 650px;
            color: #cbd5e1;
            font-size: 14px;
            line-height: 1.6;
        }

        .hero-score-box {
            min-width: 195px;
            padding: 22px;
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.07);
            text-align: center;
        }

        .hero-score-label {
            color: #94a3b8;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 1.2px;
        }

        .hero-score {
            margin: 6px 0;
            color: white;
            font-size: 41px;
            font-weight: 900;
        }

        .hero-score-caption {
            color: #94a3b8;
            font-size: 11px;
        }

        /* KPI cards */

        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }

        .kpi-card {
            min-height: 145px;
            padding: 18px 18px 16px;
            border-radius: 14px;
            background: white;
            box-shadow: 0 7px 22px rgba(15, 23, 42, 0.06);
        }

        .kpi-icon {
            font-size: 23px;
        }

        .kpi-title {
            margin-top: 10px;
            color: #64748b;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.7px;
            text-transform: uppercase;
        }

        .kpi-value {
            margin-top: 3px;
            color: #0f172a;
            font-size: 28px;
            font-weight: 900;
        }

        .kpi-subtitle {
            margin-top: 3px;
            color: #94a3b8;
            font-size: 11px;
        }

        /* Tabs and cards */

        .dashboard-tab {
            padding: 13px 17px !important;
            border: none !important;
            background: transparent !important;
            color: #64748b !important;
            font-size: 13px;
            font-weight: 700;
        }

        .dashboard-tab-selected {
            border: none !important;
            border-bottom: 3px solid #f97316 !important;
            background: white !important;
            color: #0f172a !important;
        }

        .tab-content {
            padding-top: 20px;
        }

        .two-column-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 18px;
            margin-bottom: 18px;
        }

        .chart-card {
            padding: 19px;
            border: 1px solid #edf1f5;
            border-radius: 15px;
            overflow: hidden;
            background: white;
            box-shadow: 0 7px 22px rgba(15, 23, 42, 0.045);
        }

        .section-heading {
            padding-left: 10px;
            border-left: 4px solid #f97316;
            margin-bottom: 10px;
        }

        .section-heading h2 {
            margin: 0;
            color: #0f172a;
            font-size: 17px;
            font-weight: 850;
        }

        .section-heading p {
            margin: 4px 0 0;
            color: #64748b;
            font-size: 11px;
        }

        .search-input {
            width: 100%;
            padding: 12px 14px;
            border: 1px solid #dbe3ec;
            border-radius: 9px;
            outline: none;
            color: #0f172a;
            font-size: 13px;
        }

        .search-input:focus {
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        /* Recommendations */

        .recommendation-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .recommendation-card {
            position: relative;
            padding: 16px 18px;
            border-left: 5px solid #22c55e;
            border-radius: 11px;
            background: #f8fafc;
        }

        .recommendation-card.high {
            border-left-color: #ef4444;
        }

        .recommendation-card.medium {
            border-left-color: #f59e0b;
        }

        .recommendation-card.low {
            border-left-color: #22c55e;
        }

        .priority-pill {
            float: right;
            padding: 5px 9px;
            border-radius: 15px;
            color: white;
            font-size: 9px;
            font-weight: 900;
            letter-spacing: 0.7px;
        }

        .priority-pill.high {
            background: #ef4444;
        }

        .priority-pill.medium {
            background: #f59e0b;
        }

        .priority-pill.low {
            background: #22c55e;
        }

        .recommendation-title {
            color: #0f172a;
            font-size: 14px;
            font-weight: 800;
        }

        .recommendation-description {
            max-width: 90%;
            margin-top: 5px;
            color: #64748b;
            font-size: 12px;
            line-height: 1.6;
        }

        .empty-state {
            padding: 35px;
            border-radius: 12px;
            background: #f8fafc;
            text-align: center;
        }

        .empty-title {
            color: #334155;
            font-weight: 800;
        }

        .empty-description {
            margin-top: 5px;
            color: #94a3b8;
            font-size: 12px;
        }

        .footer {
            padding: 28px 0 8px;
            color: #94a3b8;
            text-align: center;
            font-size: 11px;
        }

        /* Responsive */

        @media screen and (max-width: 1150px) {
            .sidebar {
                width: 245px;
            }

            .kpi-grid {
                grid-template-columns: repeat(3, minmax(0, 1fr));
            }
        }

        @media screen and (max-width: 850px) {
            .app-shell {
                display: block;
            }

            .sidebar {
                width: 100%;
                min-height: auto;
                height: auto;
                position: relative;
            }

            .main-content {
                padding: 20px;
            }

            .two-column-grid {
                grid-template-columns: 1fr;
            }

            .hero {
                display: block;
            }

            .hero-score-box {
                width: 100%;
                margin-top: 20px;
            }
        }

        @media screen and (max-width: 600px) {
            .kpi-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .topbar {
                display: block;
            }

            .topbar-status {
                margin-top: 12px;
            }

            .hero h1 {
                font-size: 29px;
            }
        }
    </style>
</head>

<body>
    {%app_entry%}

    <footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </footer>
</body>
</html>
"""


# ============================================================
# LAYOUT
# ============================================================

app.layout = html.Div(
    [
        dcc.Store(
            id="seed-store",
            data=42
        ),

        dcc.Interval(
            id="live-interval",
            interval=60 * 1000,
            n_intervals=0
        ),

        html.Div(
            [
                # ------------------------------------------------
                # SIDEBAR
                # ------------------------------------------------

                html.Aside(
                    [
                        html.Div(
                            [
                                html.Div(
                                    "BS",
                                    className="brand-symbol"
                                ),
                                html.Div(
                                    [
                                        html.Div(
                                            "BuildSure",
                                            className="brand-name"
                                        ),
                                        html.Div(
                                            "SITE INTELLIGENCE",
                                            className="brand-subtitle"
                                        ),
                                    ]
                                ),
                            ],
                            className="brand"
                        ),

                        html.Div(
                            "MILESTONE 1",
                            className="milestone-label"
                        ),

                        html.P(
                            "Site Risk Monitoring & Hazard Detection",
                            className="sidebar-description"
                        ),

                        html.Div(
                            className="sidebar-divider"
                        ),

                        html.Div(
                            "FILTERS",
                            className="filter-heading"
                        ),

                        html.Label(
                            "Site Zones",
                            className="filter-label"
                        ),

                        dcc.Dropdown(
                            id="zone-filter",
                            options=[
                                {
                                    "label": zone,
                                    "value": zone
                                }
                                for zone in ZONES
                            ],
                            value=ZONES,
                            multi=True,
                            clearable=True
                        ),

                        html.Label(
                            "Hazard Categories",
                            className="filter-label"
                        ),

                        dcc.Dropdown(
                            id="risk-type-filter",
                            options=[
                                {
                                    "label": risk_type,
                                    "value": risk_type
                                }
                                for risk_type in RISK_TYPES
                            ],
                            value=RISK_TYPES,
                            multi=True,
                            clearable=True
                        ),

                        html.Label(
                            "Hazard Status",
                            className="filter-label"
                        ),

                        dcc.Dropdown(
                            id="status-filter",
                            options=[
                                {
                                    "label": status,
                                    "value": status
                                }
                                for status in STATUSES
                            ],
                            value=STATUSES,
                            multi=True,
                            clearable=True
                        ),

                        html.Label(
                            "Lookback Window",
                            className="filter-label"
                        ),

                        dcc.Slider(
                            id="lookback-filter",
                            min=1,
                            max=30,
                            step=1,
                            value=30,
                            marks={
                                1: "1d",
                                7: "7d",
                                14: "14d",
                                21: "21d",
                                30: "30d",
                            },
                            className="sidebar-slider"
                        ),

                        html.Button(
                            "↻  Refresh Site Data",
                            id="refresh-button",
                            n_clicks=0,
                            className="refresh-button"
                        ),

                        html.Div(
                            [
                                html.Div(
                                    "DATA FEED",
                                    className="feed-heading"
                                ),
                                html.Div(
                                    "●  CCTV monitoring",
                                    className="feed-item"
                                ),
                                html.Div(
                                    "●  Site inspections",
                                    className="feed-item"
                                ),
                                html.Div(
                                    "●  Equipment sensors",
                                    className="feed-item"
                                ),
                                html.Div(
                                    "●  Environmental sensors",
                                    className="feed-item"
                                ),
                            ],
                            className="feed-card"
                        ),

                        html.Div(
                            "Synthetic data is used for this Milestone 1 prototype.",
                            className="sidebar-footer"
                        ),
                    ],
                    className="sidebar"
                ),

                # ------------------------------------------------
                # MAIN CONTENT
                # ------------------------------------------------

                html.Main(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            "CONSTRUCTION RISK INTELLIGENCE",
                                            className="topbar-eyebrow"
                                        ),
                                        html.Div(
                                            "Site Risk Command Center",
                                            className="topbar-title"
                                        ),
                                    ]
                                ),
                                html.Div(
                                    [
                                        html.Span(
                                            "● LIVE MONITORING",
                                            className="live-pill"
                                        ),
                                        html.Span(
                                            id="last-updated",
                                            className="sync-time"
                                        ),
                                    ],
                                    className="topbar-status"
                                ),
                            ],
                            className="topbar"
                        ),

                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                "MILESTONE 1 ",
                                                html.Span(
                                                    "SITE RISK AGENT",
                                                    className="hero-tag"
                                                ),
                                            ],
                                            className="hero-label"
                                        ),

                                        html.H1(
                                            [
                                                "See risk before ",
                                                html.Span(
                                                    "it becomes an incident.",
                                                    className="hero-highlight"
                                                ),
                                            ]
                                        ),

                                        html.P(
                                            "A live operational view of site hazards, "
                                            "risk severity, equipment exposure and "
                                            "environmental conditions.",
                                            className="hero-description"
                                        ),
                                    ],
                                    className="hero-content"
                                ),

                                html.Div(
                                    [
                                        html.Div(
                                            "SITE RISK INDEX",
                                            className="hero-score-label"
                                        ),
                                        html.Div(
                                            id="hero-score",
                                            className="hero-score"
                                        ),
                                        html.Div(
                                            "AI-computed exposure score",
                                            className="hero-score-caption"
                                        ),
                                    ],
                                    className="hero-score-box"
                                ),
                            ],
                            className="hero"
                        ),

                        html.Div(
                            id="kpi-row",
                            className="kpi-grid"
                        ),

                        dcc.Tabs(
                            id="dashboard-tabs",
                            value="overview",
                            children=[
                                # ------------------------------------------------
                                # OVERVIEW TAB
                                # ------------------------------------------------

                                dcc.Tab(
                                    label="Risk Overview",
                                    value="overview",
                                    className="dashboard-tab",
                                    selected_className="dashboard-tab-selected",
                                    children=html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(
                                                        [
                                                            section_heading(
                                                                "Probability × Impact",
                                                                "Inherent risk distribution across detected hazards."
                                                            ),
                                                            dcc.Graph(
                                                                id="inherent-heatmap",
                                                                config={
                                                                    "displayModeBar": False
                                                                }
                                                            ),
                                                        ],
                                                        className="chart-card"
                                                    ),

                                                    html.Div(
                                                        [
                                                            section_heading(
                                                                "Residual Risk",
                                                                "Mitigated hazards remaining after corrective action."
                                                            ),
                                                            dcc.Graph(
                                                                id="residual-heatmap",
                                                                config={
                                                                    "displayModeBar": False
                                                                }
                                                            ),
                                                        ],
                                                        className="chart-card"
                                                    ),
                                                ],
                                                className="two-column-grid"
                                            ),

                                            html.Div(
                                                [
                                                    html.Div(
                                                        [
                                                            section_heading(
                                                                "Hazards by Category"
                                                            ),
                                                            dcc.Graph(
                                                                id="risk-distribution",
                                                                config={
                                                                    "displayModeBar": False
                                                                }
                                                            ),
                                                        ],
                                                        className="chart-card"
                                                    ),

                                                    html.Div(
                                                        [
                                                            section_heading(
                                                                "Hazard Status"
                                                            ),
                                                            dcc.Graph(
                                                                id="status-chart",
                                                                config={
                                                                    "displayModeBar": False
                                                                }
                                                            ),
                                                        ],
                                                        className="chart-card"
                                                    ),
                                                ],
                                                className="two-column-grid"
                                            ),
                                        ],
                                        className="tab-content"
                                    )
                                ),

                                # ------------------------------------------------
                                # MAP TAB
                                # ------------------------------------------------

                                dcc.Tab(
                                    label="Site Risk Map",
                                    value="map",
                                    className="dashboard-tab",
                                    selected_className="dashboard-tab-selected",
                                    children=html.Div(
                                        [
                                            html.Div(
                                                [
                                                    section_heading(
                                                        "Construction Site Risk Map",
                                                        "Bubble size represents hazard volume. Color represents average severity."
                                                    ),
                                                    dcc.Graph(
                                                        id="site-map",
                                                        config={
                                                            "displayModeBar": False
                                                        }
                                                    ),
                                                ],
                                                className="chart-card"
                                            ),

                                            html.Div(
                                                [
                                                    section_heading(
                                                        "Zone Risk Prioritization"
                                                    ),
                                                    dash_table.DataTable(
                                                        id="zone-table",
                                                        columns=[
                                                            {
                                                                "name": "Zone",
                                                                "id": "zone"
                                                            },
                                                            {
                                                                "name": "Hazards",
                                                                "id": "hazards"
                                                            },
                                                            {
                                                                "name": "Avg Severity",
                                                                "id": "avg_severity"
                                                            },
                                                            {
                                                                "name": "Risk Level",
                                                                "id": "risk_level"
                                                            },
                                                        ],
                                                        data=[],
                                                        sort_action="native",
                                                        page_size=8,
                                                        style_table={
                                                            "overflowX": "auto"
                                                        },
                                                        style_cell={
                                                            "padding": "13px",
                                                            "fontFamily": "Arial",
                                                            "fontSize": "13px",
                                                            "textAlign": "left"
                                                        },
                                                        style_header={
                                                            "backgroundColor": "#f1f5f9",
                                                            "fontWeight": "700",
                                                            "color": "#334155"
                                                        },
                                                        style_data_conditional=[
                                                            {
                                                                "if": {
                                                                    "filter_query": '{risk_level} = "Critical"',
                                                                    "column_id": "risk_level"
                                                                },
                                                                "color": "#7f1d1d",
                                                                "fontWeight": "700"
                                                            },
                                                            {
                                                                "if": {
                                                                    "filter_query": '{risk_level} = "High"',
                                                                    "column_id": "risk_level"
                                                                },
                                                                "color": "#ef4444",
                                                                "fontWeight": "700"
                                                            },
                                                            {
                                                                "if": {
                                                                    "filter_query": '{risk_level} = "Medium-High"',
                                                                    "column_id": "risk_level"
                                                                },
                                                                "color": "#f97316",
                                                                "fontWeight": "700"
                                                            },
                                                            {
                                                                "if": {
                                                                    "filter_query": '{risk_level} = "Medium"',
                                                                    "column_id": "risk_level"
                                                                },
                                                                "color": "#ca8a04",
                                                                "fontWeight": "700"
                                                            },
                                                            {
                                                                "if": {
                                                                    "filter_query": '{risk_level} = "Low"',
                                                                    "column_id": "risk_level"
                                                                },
                                                                "color": "#16a34a",
                                                                "fontWeight": "700"
                                                            },
                                                        ],
                                                    ),
                                                ],
                                                className="chart-card"
                                            ),
                                        ],
                                        className="tab-content"
                                    )
                                ),

                                # ------------------------------------------------
                                # HAZARD DETECTION TAB
                                # ------------------------------------------------

                                dcc.Tab(
                                    label="Hazard Detection",
                                    value="hazards",
                                    className="dashboard-tab",
                                    selected_className="dashboard-tab-selected",
                                    children=html.Div(
                                        [
                                            html.Div(
                                                [
                                                    section_heading(
                                                        "Detected Hazard Records",
                                                        "Search and investigate records identified by the Site Risk Agent."
                                                    ),

                                                    dcc.Input(
                                                        id="hazard-search",
                                                        type="text",
                                                        placeholder="Search zone, hazard type or description...",
                                                        className="search-input"
                                                    ),

                                                    dash_table.DataTable(
                                                        id="hazard-table",
                                                        columns=[
                                                            {
                                                                "name": "Risk ID",
                                                                "id": "risk_id"
                                                            },
                                                            {
                                                                "name": "Zone",
                                                                "id": "zone"
                                                            },
                                                            {
                                                                "name": "Risk Type",
                                                                "id": "risk_type"
                                                            },
                                                            {
                                                                "name": "Description",
                                                                "id": "description"
                                                            },
                                                            {
                                                                "name": "Score",
                                                                "id": "severity_score"
                                                            },
                                                            {
                                                                "name": "Severity",
                                                                "id": "severity_label"
                                                            },
                                                            {
                                                                "name": "Status",
                                                                "id": "status"
                                                            },
                                                            {
                                                                "name": "Detected At",
                                                                "id": "detected_at"
                                                            },
                                                        ],
                                                        data=[],
                                                        sort_action="native",
                                                        filter_action="native",
                                                        page_size=10,
                                                        style_table={
                                                            "overflowX": "auto",
                                                            "marginTop": "16px"
                                                        },
                                                        style_cell={
                                                            "padding": "12px",
                                                            "fontFamily": "Arial",
                                                            "fontSize": "12px",
                                                            "textAlign": "left",
                                                            "whiteSpace": "normal",
                                                            "minWidth": "100px"
                                                        },
                                                        style_header={
                                                            "backgroundColor": "#f1f5f9",
                                                            "fontWeight": "700",
                                                            "color": "#334155"
                                                        },
                                                        style_data_conditional=[
                                                            {
                                                                "if": {
                                                                    "filter_query": '{severity_label} = "Critical"',
                                                                    "column_id": "severity_label"
                                                                },
                                                                "color": "#7f1d1d",
                                                                "fontWeight": "700"
                                                            },
                                                            {
                                                                "if": {
                                                                    "filter_query": '{severity_label} = "High"',
                                                                    "column_id": "severity_label"
                                                                },
                                                                "color": "#ef4444",
                                                                "fontWeight": "700"
                                                            },
                                                            {
                                                                "if": {
                                                                    "filter_query": '{severity_label} = "Medium-High"',
                                                                    "column_id": "severity_label"
                                                                },
                                                                "color": "#f97316",
                                                                "fontWeight": "700"
                                                            },
                                                            {
                                                                "if": {
                                                                    "filter_query": '{status} = "Open"',
                                                                    "column_id": "status"
                                                                },
                                                                "color": "#ef4444",
                                                                "fontWeight": "700"
                                                            },
                                                            {
                                                                "if": {
                                                                    "filter_query": '{status} = "Mitigated"',
                                                                    "column_id": "status"
                                                                },
                                                                "color": "#16a34a",
                                                                "fontWeight": "700"
                                                            },
                                                        ],
                                                    ),
                                                ],
                                                className="chart-card"
                                            ),

                                            html.Div(
                                                [
                                                    section_heading(
                                                        "Hazard Detection Trend"
                                                    ),
                                                    dcc.Graph(
                                                        id="hazard-trend",
                                                        config={
                                                            "displayModeBar": False
                                                        }
                                                    ),
                                                ],
                                                className="chart-card"
                                            ),
                                        ],
                                        className="tab-content"
                                    )
                                ),

                                # ------------------------------------------------
                                # EQUIPMENT AND ENVIRONMENT TAB
                                # ------------------------------------------------

                                dcc.Tab(
                                    label="Equipment & Environment",
                                    value="monitoring",
                                    className="dashboard-tab",
                                    selected_className="dashboard-tab-selected",
                                    children=html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(
                                                        [
                                                            section_heading(
                                                                "Equipment Risk Monitoring",
                                                                "Current equipment exposure and inspection status."
                                                            ),
                                                            dcc.Graph(
                                                                id="equipment-chart",
                                                                config={
                                                                    "displayModeBar": False
                                                                }
                                                            ),
                                                        ],
                                                        className="chart-card"
                                                    ),

                                                    html.Div(
                                                        [
                                                            section_heading(
                                                                "Equipment Register"
                                                            ),
                                                            dash_table.DataTable(
                                                                id="equipment-table",
                                                                columns=[
                                                                    {
                                                                        "name": "Equipment",
                                                                        "id": "equipment_name"
                                                                    },
                                                                    {
                                                                        "name": "Zone",
                                                                        "id": "zone"
                                                                    },
                                                                    {
                                                                        "name": "Risk Score",
                                                                        "id": "risk_score"
                                                                    },
                                                                    {
                                                                        "name": "Status",
                                                                        "id": "status"
                                                                    },
                                                                    {
                                                                        "name": "Inspection Age",
                                                                        "id": "last_inspection_days_ago"
                                                                    },
                                                                ],
                                                                data=[],
                                                                sort_action="native",
                                                                page_size=10,
                                                                style_table={
                                                                    "overflowX": "auto"
                                                                },
                                                                style_cell={
                                                                    "padding": "12px",
                                                                    "fontFamily": "Arial",
                                                                    "fontSize": "12px",
                                                                    "textAlign": "left"
                                                                },
                                                                style_header={
                                                                    "backgroundColor": "#f1f5f9",
                                                                    "fontWeight": "700",
                                                                    "color": "#334155"
                                                                },
                                                            ),
                                                        ],
                                                        className="chart-card"
                                                    ),
                                                ],
                                                className="two-column-grid"
                                            ),

                                            html.Div(
                                                [
                                                    html.Div(
                                                        [
                                                            section_heading(
                                                                "Environmental Risk by Zone"
                                                            ),
                                                            dcc.Graph(
                                                                id="environment-chart",
                                                                config={
                                                                    "displayModeBar": False
                                                                }
                                                            ),
                                                        ],
                                                        className="chart-card"
                                                    ),

                                                    html.Div(
                                                        [
                                                            section_heading(
                                                                "Environmental Risk Index"
                                                            ),
                                                            dcc.Graph(
                                                                id="environment-gauge",
                                                                config={
                                                                    "displayModeBar": False
                                                                }
                                                            ),
                                                        ],
                                                        className="chart-card"
                                                    ),
                                                ],
                                                className="two-column-grid"
                                            ),
                                        ],
                                        className="tab-content"
                                    )
                                ),

                                # ------------------------------------------------
                                # RECOMMENDATIONS TAB
                                # ------------------------------------------------

                                dcc.Tab(
                                    label="AI Recommendations",
                                    value="recommendations",
                                    className="dashboard-tab",
                                    selected_className="dashboard-tab-selected",
                                    children=html.Div(
                                        [
                                            html.Div(
                                                [
                                                    section_heading(
                                                        "Site Risk Recommendations",
                                                        "Rule-based recommendations generated from current site observations."
                                                    ),
                                                    html.Div(
                                                        id="recommendations",
                                                        className="recommendation-list"
                                                    ),
                                                ],
                                                className="chart-card"
                                            ),

                                            html.Div(
                                                [
                                                    section_heading(
                                                        "Site Activity Monitoring"
                                                    ),
                                                    dcc.Graph(
                                                        id="activity-chart",
                                                        config={
                                                            "displayModeBar": False
                                                        }
                                                    ),
                                                ],
                                                className="chart-card"
                                            ),
                                        ],
                                        className="tab-content"
                                    )
                                ),
                            ]
                        ),

                        html.Footer(
                            "BuildSure AI · Milestone 1 · Site Risk Monitoring & Hazard Detection",
                            className="footer"
                        ),
                    ],
                    className="main-content"
                ),
            ],
            className="app-shell"
        ),
    ]
)


# ============================================================
# REFRESH DATA CALLBACK
# ============================================================

@app.callback(
    Output("seed-store", "data"),
    [
        Input("refresh-button", "n_clicks"),
        Input("live-interval", "n_intervals"),
    ]
)
def refresh_data(n_clicks, n_intervals):
    n_clicks = n_clicks or 0
    n_intervals = n_intervals or 0

    return (
        42
        + (n_clicks * 7919)
        + (n_intervals * 104729)
    )


# ============================================================
# MAIN DASHBOARD CALLBACK
# ============================================================

@app.callback(
    [
        Output("kpi-row", "children"),
        Output("hero-score", "children"),
        Output("inherent-heatmap", "figure"),
        Output("residual-heatmap", "figure"),
        Output("risk-distribution", "figure"),
        Output("status-chart", "figure"),
        Output("site-map", "figure"),
        Output("zone-table", "data"),
        Output("hazard-table", "data"),
        Output("hazard-trend", "figure"),
        Output("equipment-chart", "figure"),
        Output("equipment-table", "data"),
        Output("environment-chart", "figure"),
        Output("environment-gauge", "figure"),
        Output("recommendations", "children"),
        Output("activity-chart", "figure"),
        Output("last-updated", "children"),
    ],
    [
        Input("seed-store", "data"),
        Input("zone-filter", "value"),
        Input("risk-type-filter", "value"),
        Input("status-filter", "value"),
        Input("lookback-filter", "value"),
        Input("hazard-search", "value"),
    ]
)
def update_dashboard(
    seed,
    selected_zones,
    selected_types,
    selected_statuses,
    lookback,
    search_text,
):
    risk_df, equipment_df, environment_df, activity_df = (
        generate_data(int(seed))
    )

    selected_zones = selected_zones or ZONES
    selected_types = selected_types or RISK_TYPES
    selected_statuses = selected_statuses or STATUSES
    lookback = int(lookback or 30)

    cutoff = (
        pd.Timestamp.now()
        - pd.Timedelta(days=lookback)
    )

    filtered_risks = risk_df[
        risk_df["zone"].isin(selected_zones)
        & risk_df["risk_type"].isin(selected_types)
        & risk_df["status"].isin(selected_statuses)
        & (risk_df["detected_at"] >= cutoff)
    ].copy()

    filtered_equipment = equipment_df[
        equipment_df["zone"].isin(selected_zones)
    ].copy()

    filtered_environment = environment_df[
        environment_df["zone"].isin(selected_zones)
    ].copy()

    # --------------------------------------------------------
    # KPI calculations
    # --------------------------------------------------------

    active_risks = int(
        (filtered_risks["status"] == "Open").sum()
    )

    zone_severity = (
        filtered_risks
        .groupby("zone")["severity_score"]
        .mean()
    )

    high_risk_zones = int(
        (zone_severity >= 13).sum()
    )

    hazards_detected = int(
        len(filtered_risks)
    )

    if filtered_risks.empty:
        site_risk_score = 0
    else:
        site_risk_score = int(
            round(
                filtered_risks["severity_score"].mean()
                / 25
                * 100
            )
        )

    equipment_at_risk = int(
        filtered_equipment["status"]
        .isin(
            [
                "Critical",
                "Needs Inspection"
            ]
        )
        .sum()
    )

    kpis = [
        create_kpi(
            "⚠️",
            "Active Risks",
            active_risks,
            "Currently open",
            "#ef4444"
        ),
        create_kpi(
            "🚧",
            "High-Risk Zones",
            high_risk_zones,
            "Average severity ≥ 13",
            "#f97316"
        ),
        create_kpi(
            "🔍",
            "Hazards Detected",
            hazards_detected,
            f"Last {lookback} days",
            "#3b82f6"
        ),
        create_kpi(
            "📊",
            "Site Risk Score",
            f"{site_risk_score}/100",
            "AI-computed index",
            "#8b5cf6"
        ),
        create_kpi(
            "🛠️",
            "Equipment at Risk",
            equipment_at_risk,
            "Needs attention",
            "#eab308"
        ),
    ]

    # --------------------------------------------------------
    # Zone summary
    # --------------------------------------------------------

    zone_summary = build_zone_summary(
        filtered_risks
    )

    zone_table = zone_summary[
        [
            "zone",
            "hazards",
            "avg_severity",
            "risk_level",
        ]
    ].copy()

    zone_table["avg_severity"] = zone_table[
        "avg_severity"
    ].round(1)

    # --------------------------------------------------------
    # Hazard table
    # --------------------------------------------------------

    hazard_table = filtered_risks.sort_values(
        "detected_at",
        ascending=False
    ).copy()

    if search_text:
        search_text = str(search_text)

        search_mask = (
            hazard_table.astype(str)
            .apply(
                lambda column: column.str.contains(
                    search_text,
                    case=False,
                    regex=False,
                    na=False
                )
            )
            .any(axis=1)
        )

        hazard_table = hazard_table[
            search_mask
        ]

    hazard_table["detected_at"] = (
        pd.to_datetime(
            hazard_table["detected_at"]
        ).dt.strftime(
            "%d %b %Y %H:%M"
        )
    )

    hazard_table = hazard_table[
        [
            "risk_id",
            "zone",
            "risk_type",
            "description",
            "severity_score",
            "severity_label",
            "status",
            "detected_at",
        ]
    ]

    # --------------------------------------------------------
    # Equipment table
    # --------------------------------------------------------

    equipment_table = filtered_equipment[
        [
            "equipment_name",
            "zone",
            "risk_score",
            "status",
            "last_inspection_days_ago",
        ]
    ].sort_values(
        "risk_score",
        ascending=False
    )

    return (
        kpis,
        f"{site_risk_score}/100",
        build_heatmap(filtered_risks),
        build_heatmap(
            filtered_risks[
                filtered_risks["status"] == "Mitigated"
            ]
        ),
        build_risk_distribution(filtered_risks),
        build_status_chart(filtered_risks),
        build_site_map(zone_summary),
        records_as_json(zone_table),
        records_as_json(hazard_table),
        build_hazard_trend(
            filtered_risks,
            lookback
        ),
        build_equipment_chart(
            filtered_equipment
        ),
        records_as_json(equipment_table),
        build_environment_chart(
            filtered_environment
        ),
        build_environment_gauge(
            filtered_environment
        ),
        create_recommendations(
            filtered_risks,
            filtered_equipment,
            filtered_environment
        ),
        build_activity_chart(
            activity_df,
            filtered_risks,
            lookback
        ),
        "Last sync · "
        + datetime.now().strftime(
            "%d %b %Y, %H:%M:%S"
        ),
    )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=8050
    )