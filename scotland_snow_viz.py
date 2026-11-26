"""
Scotland Autumn 2026 Snow Visualiser
Fetches daily snowfall & snow-depth from the Open-Meteo archive API for
several Scottish stations, then renders interactive Plotly charts in Gradio.
"""

import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import date

AUTUMN_START    = "2026-09-01"
ARCHIVE_LAG     = 5                        # Open-Meteo archive has ~5 day lag
from datetime import timedelta
AUTUMN_END = (date.today() - timedelta(days=ARCHIVE_LAG)).isoformat()

STATIONS = {
    "Cairngorm Summit":   (57.117, -3.643),
    "Aviemore":           (57.188, -3.830),
    "Fort William":       (56.819, -5.105),
    "Inverness":          (57.477, -4.224),
    "Aberdeen":           (57.149, -2.094),
    "Edinburgh":          (55.953, -3.189),
    "Glasgow":            (55.864, -4.252),
}

PALETTE = px.colors.qualitative.Bold


def fetch_station(name: str, lat: float, lon: float) -> pd.DataFrame:
    params = {
        "latitude":   lat,
        "longitude":  lon,
        "start_date": AUTUMN_START,
        "end_date":   AUTUMN_END,
        "daily": ["snowfall_sum", "snow_depth_max", "precipitation_sum",
                  "temperature_2m_max", "temperature_2m_min"],
        "timezone": "Europe/London",
    }
    r = requests.get("https://archive-api.open-meteo.com/v1/archive", params=params, timeout=15)
    r.raise_for_status()
    data = r.json()["daily"]
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["time"])
    df["location"] = name
    df = df.drop(columns=["time"])
    df = df.rename(columns={
        "snowfall_sum":        "snowfall_cm",
        "snow_depth_max":      "snow_depth_m",
        "precipitation_sum":   "precip_mm",
        "temperature_2m_max":  "temp_max_c",
        "temperature_2m_min":  "temp_min_c",
    })
    df["snowfall_cm"]  = df["snowfall_cm"].fillna(0)
    df["snow_depth_m"] = df["snow_depth_m"].fillna(0)
    return df


def load_all_data() -> pd.DataFrame:
    frames = []
    for name, (lat, lon) in STATIONS.items():
        try:
            frames.append(fetch_station(name, lat, lon))
        except Exception as e:
            print(f"[warn] could not fetch {name}: {e}")
    return pd.concat(frames, ignore_index=True)


# ── Chart builders ────────────────────────────────────────────────────────────

def fig_daily_snowfall(df: pd.DataFrame) -> go.Figure:
    fig = px.line(
        df,
        x="date", y="snowfall_cm", color="location",
        title="Daily Snowfall — Scotland Autumn 2026",
        labels={"snowfall_cm": "Snowfall (cm)", "date": "Date", "location": "Station"},
        color_discrete_sequence=PALETTE,
        height=500,
    )
    fig.update_traces(line_width=2)
    _style(fig)
    return fig


def fig_cumulative_snowfall(df: pd.DataFrame) -> go.Figure:
    sorted_df = df.sort_values(["location", "date"])
    sorted_df = sorted_df.copy()
    sorted_df["cum_snow"] = sorted_df.groupby("location")["snowfall_cm"].cumsum()
    cum = sorted_df
    fig = px.line(
        cum,
        x="date", y="cum_snow", color="location",
        title="Cumulative Snowfall — Scotland Autumn 2026",
        labels={"cum_snow": "Cumulative snowfall (cm)", "date": "Date", "location": "Station"},
        color_discrete_sequence=PALETTE,
        height=500,
    )
    fig.update_traces(line_width=2)
    _style(fig)
    return fig


def fig_snow_depth(df: pd.DataFrame) -> go.Figure:
    fig = px.area(
        df,
        x="date", y="snow_depth_m", color="location",
        title="Snow Depth on the Ground — Scotland Autumn 2026",
        labels={"snow_depth_m": "Snow depth (m)", "date": "Date", "location": "Station"},
        color_discrete_sequence=PALETTE,
        height=500,
    )
    _style(fig)
    return fig


def fig_total_bar(df: pd.DataFrame) -> go.Figure:
    totals = (
        df.groupby("location")["snowfall_cm"]
        .sum()
        .reset_index()
        .sort_values("snowfall_cm", ascending=True)
    )
    fig = px.bar(
        totals,
        x="snowfall_cm", y="location",
        orientation="h",
        title="Total Autumn 2026 Snowfall by Station",
        labels={"snowfall_cm": "Total snowfall (cm)", "location": "Station"},
        color="snowfall_cm",
        color_continuous_scale="Blues",
        height=420,
    )
    fig.update_layout(coloraxis_showscale=False)
    _style(fig)
    return fig


def fig_temperature(df: pd.DataFrame) -> go.Figure:
    # Aggregate daily min/max across all stations for a Scotland-wide picture
    agg = df.groupby("date").agg(
        temp_max=("temp_max_c", "max"),
        temp_min=("temp_min_c", "min"),
    ).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=agg["date"], y=agg["temp_max"],
        mode="lines", name="Max temp (across stations)",
        line=dict(color="#e74c3c", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=agg["date"], y=agg["temp_min"],
        mode="lines", name="Min temp (across stations)",
        line=dict(color="#3498db", width=2),
        fill="tonexty", fillcolor="rgba(52,152,219,0.08)",
    ))
    fig.add_hline(y=0, line_dash="dot", line_color="grey", annotation_text="0 °C")
    fig.update_layout(
        title="Temperature Range Across Scottish Stations — Autumn 2026",
        xaxis_title="Date",
        yaxis_title="Temperature (°C)",
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    _style(fig)
    return fig


def _style(fig: go.Figure):
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="#f8f9fa",
        font_size=13,
        hovermode="x unified",
    )


# ── Gradio app ────────────────────────────────────────────────────────────────

def build_charts():
    status = "Fetching weather data from Open-Meteo…"
    yield (
        status,
        go.Figure(), go.Figure(), go.Figure(), go.Figure(), go.Figure(),
    )

    df = load_all_data()
    n_days  = df["date"].nunique()
    n_locs  = df["location"].nunique()
    total   = df["snowfall_cm"].sum()
    deepest = df.loc[df["snow_depth_m"].idxmax()]

    summary = (
        f"Loaded {n_days} days × {n_locs} stations.  "
        f"Total recorded snowfall across all stations: **{total:.1f} cm**.  "
        f"Deepest snow: **{deepest['snow_depth_m']:.2f} m** at {deepest['location']} "
        f"on {deepest['date'].strftime('%d %b %Y')}."
    )

    yield (
        summary,
        fig_daily_snowfall(df),
        fig_cumulative_snowfall(df),
        fig_snow_depth(df),
        fig_total_bar(df),
        fig_temperature(df),
    )


with gr.Blocks(title="Scotland Snow — Autumn 2026", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        "# Scotland Snow — Autumn 2026\n"
        "Daily snowfall and snow depth for seven Scottish stations, "
        "sourced from the [Open-Meteo](https://open-meteo.com) archive API."
    )

    status_md = gr.Markdown("Click **Load data** to begin.")
    load_btn  = gr.Button("Load data", variant="primary", size="lg")

    with gr.Tabs():
        with gr.Tab("Daily Snowfall"):
            p1 = gr.Plot()
        with gr.Tab("Cumulative Snowfall"):
            p2 = gr.Plot()
        with gr.Tab("Snow Depth"):
            p3 = gr.Plot()
        with gr.Tab("Station Totals"):
            p4 = gr.Plot()
        with gr.Tab("Temperature"):
            p5 = gr.Plot()

    load_btn.click(
        fn=build_charts,
        inputs=[],
        outputs=[status_md, p1, p2, p3, p4, p5],
    )

if __name__ == "__main__":
    demo.launch()
