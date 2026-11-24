"""Plotly figures for the dashboard. Each function takes plain inputs
(a source object, a year, a pod...) and returns a go.Figure, so the charts can
be tried out in a notebook without running the app."""
import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .config import CURYR, MONTHS, REFERENCE_YEAR, TODAY
from .salmon import albion_chinook, bonneville
from .sightings import sighting_timing, weekly_sighting_days

# ---- Shared look ------------------------------------------------------------
FONT = "Raleway, sans-serif"
INK = "#1f2933"
GRID = "#e6e6e6"
YEAR_COLORS = px.colors.qualitative.Plotly  # [0] selected year, [1] year before, [2] two before
HIST_COLOR = YEAR_COLORS[3]
SRKW_COLOR = "#6250d6"
SRKW_CANDIDATE_COLOR = "rgba(98,80,214,0.35)"
SITE_COLOR = "#D85A30"
MONTH_COLORS = px.colors.sample_colorscale("Viridis", [i / 11 for i in range(12)])
MONTH_COLORS = MONTH_COLORS[:9] + ["#e8a33d", "#d9764a", "#c45a5a"]  # warm autumn end
MONTH_SCALE = [[i / 11, c] for i, c in enumerate(MONTH_COLORS)]

# Run-timing series: color and dash per source key
TIMING_STYLE = {
    "srkw": (SRKW_COLOR, "solid"),
    "albion-chinook": ("#2a78d6", "solid"),
    "bonneville-spring": ("#eb6834", "dot"),
    "bonneville-summer": ("#eb6834", "dash"),
    "bonneville-fall": ("#eb6834", "solid"),
    "lake-washington": ("#1baf7a", "solid"),
    "ps-hatcheries": ("#c98500", "dashdot"),
    "albion-chum": ("#d55181", "dot"),
}


def _base_layout(fig, height=None, **extra):
    fig.update_layout(
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family=FONT, size=12, color=INK),
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="left", x=0,
                    font=dict(size=11)),
        hovermode="x unified",
        **({"height": height} if height else {}), **extra)
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor="#999")
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


# Light and dark page themes. Figures are built in the light colours, then
# apply_theme() re-colours them when the page is in dark mode.
THEMES = {
    "light": dict(bg="white", ink=INK, grid=GRID, axis="#999", map_style="carto-positron",
                  button_bg="#f4f6f7", button_border="#c9ced3"),
    "dark": dict(bg="#111418", ink="#e6e8eb", grid="#2a2f36", axis="#5c6670", map_style="carto-darkmatter",
                 button_bg="#1f242b", button_border="#3a424c"),
}


def apply_theme(fig, theme="light"):
    t = THEMES.get(theme, THEMES["light"])
    fig.update_layout(paper_bgcolor=t["bg"], plot_bgcolor=t["bg"], font_color=t["ink"])
    fig.update_xaxes(linecolor=t["axis"])
    fig.update_yaxes(gridcolor=t["grid"], linecolor=t["axis"])
    if fig.layout.map.style:
        fig.update_layout(map_style=t["map_style"])
    for menu in fig.layout.updatemenus:
        menu.update(bgcolor=t["button_bg"], bordercolor=t["button_border"], font_color=t["ink"])
    for slider in fig.layout.sliders:
        slider.update(bgcolor=t["button_bg"], bordercolor=t["button_border"], font_color=t["ink"],
                      activebgcolor=t["axis"])
        slider.currentvalue.update(font_color=t["ink"])
    return fig


def doy_label(doy):
    """Day of year -> 'Aug 20' (non-leap year)."""
    d = pd.Timestamp(2025, 1, 1) + pd.Timedelta(days=int(doy) - 1)
    return f"{MONTHS[d.month - 1]} {d.day}"


# ---- Salmon monitor (with weekly sighting-day bars on top) -------------------
def _sighting_bars(fig, year, pod, row):
    w = weekly_sighting_days(year, pod)
    x = pd.Timestamp(REFERENCE_YEAR, 1, 1) + pd.to_timedelta(w["week"] * 7 + 3, unit="D")
    fig.add_trace(go.Bar(x=x, y=w["confirmed"], name="Orca sighting days", marker_color=SRKW_COLOR,
                         hovertemplate="%{y} day(s)<extra>confirmed</extra>", legendgroup="srkw"),
                  row=row, col=1)
    if w["candidate"].sum():
        fig.add_trace(go.Bar(x=x, y=w["candidate"], name="+ candidate days",
                             marker_color=SRKW_CANDIDATE_COLOR, legendgroup="srkw",
                             hovertemplate="%{y} day(s)<extra>candidate only</extra>"),
                      row=row, col=1)
    fig.update_yaxes(range=[0, 7], tickvals=[0, 7], title_text="Orca days", row=row, col=1)


def _new_monitor_figure(secondary=False):
    return make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.22, 0.78],
                         vertical_spacing=0.04,
                         specs=[[{}], [{"secondary_y": secondary}]])


def salmon_monitor(source, year, pod="All pods"):
    """The selected year and the two before it, plus the mean of all earlier
    years, for one salmon source; weekly orca sighting days above it."""
    fig = _new_monitor_figure()
    _sighting_bars(fig, year, pod, row=1)
    tbl = source.by_day
    for offset in (2, 1, 0):
        y = year - offset
        col = f"v{y}"
        if col in tbl:
            fig.add_trace(go.Scatter(x=tbl["x"], y=tbl[col], name=str(y), mode="lines+markers",
                                     connectgaps=True, marker=dict(size=4, color=YEAR_COLORS[offset]),
                                     line=dict(color=YEAR_COLORS[offset], width=2 if offset == 0 else 1.5),
                                     opacity=0.85),
                          row=2, col=1)
    hist_years = [y for y in source.years() if y < year - 2]
    hist = source.history_mean(hist_years)
    if hist is not None:
        fig.add_trace(go.Scatter(x=tbl["x"], y=hist, mode="lines", connectgaps=True,
                                 name=f"Historical mean ({hist_years[0]}-{hist_years[-1]})",
                                 line=dict(color=HIST_COLOR, dash="dash", width=2)),
                      row=2, col=1)
    has_data = tbl.drop(columns=["x"]).filter(regex=r"^v\d{4}$").notna().any(axis=1)
    lo, hi = tbl.loc[has_data, "x"].min(), tbl.loc[has_data, "x"].max()
    fig.update_xaxes(range=[lo - pd.Timedelta(days=5), hi + pd.Timedelta(days=5)],
                     tickformat="%b", dtick="M1")
    fig.update_yaxes(title_text=source.units, row=2, col=1)
    fig.update_layout(barmode="stack", bargap=0.15)
    return _base_layout(fig, height=520)


def albion_vs_bonneville(year, pod="All pods"):
    """Albion Chinook CPUE (left axis) and Bonneville counts (right axis) for
    one year against their historical means. Early in the current year, when
    little has been counted, the previous year is shown as well."""
    fig = _new_monitor_figure(secondary=True)
    _sighting_bars(fig, year, pod, row=1)
    years = [year] + ([year - 1] if year == CURYR and TODAY.month <= 4 else [])
    for src, axis2, colors in [(albion_chinook, False, (0, 1, 2)), (bonneville, True, (3, 4, 5))]:
        tbl = src.by_day
        for i, y in enumerate(years):
            if f"v{y}" in tbl:
                fig.add_trace(go.Scatter(x=tbl["x"], y=tbl[f"v{y}"], mode="lines+markers",
                                         name=f"{src.label.split(' (')[0]} {y}", connectgaps=True,
                                         marker=dict(size=4, color=YEAR_COLORS[colors[i]]),
                                         line=dict(color=YEAR_COLORS[colors[i]])),
                              row=2, col=1, secondary_y=axis2)
        hist_years = [y for y in src.years() if y < year - 2]
        fig.add_trace(go.Scatter(x=tbl["x"], y=src.history_mean(hist_years), mode="lines",
                                 name=f"{src.label.split(' (')[0]} historical mean", connectgaps=True,
                                 line=dict(color=YEAR_COLORS[colors[2]], dash="dash")),
                      row=2, col=1, secondary_y=axis2)
    fig.update_xaxes(range=[pd.Timestamp(REFERENCE_YEAR, 1, 1), pd.Timestamp(REFERENCE_YEAR, 12, 31)],
                     tickformat="%b", dtick="M1")
    fig.update_yaxes(title_text="CPUE (Albion)", row=2, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Count (Bonneville)", row=2, col=1, secondary_y=True, showgrid=False)
    fig.update_layout(barmode="stack", bargap=0.15)
    return _base_layout(fig, height=520)


# ---- Sightings map ------------------------------------------------------------
def map_view(df):
    """Center and zoom that fit the middle 96% of the sightings, so one
    far-away report doesn't zoom the map out."""
    if df.empty:
        return dict(lat=48.3, lon=-123.0), 6
    lat_lo, lat_hi = df["latitude"].quantile([0.02, 0.98])
    lon_lo, lon_hi = df["longitude"].quantile([0.02, 0.98])
    lat_span = max(lat_hi - lat_lo, 0.2) * 1.15
    lon_span = max(lon_hi - lon_lo, 0.2) * 1.15
    zoom = min(math.log2(360 / lon_span), math.log2(170 / lat_span)) - 0.6
    return dict(lat=(lat_lo + lat_hi) / 2, lon=(lon_lo + lon_hi) / 2), max(3, min(zoom, 10))


def _site_trace(sources):
    rows = [(s.key, s.label, name, lat, lon) for s in sources for name, lat, lon in s.sites]
    keys, labels, names, lats, lons = zip(*rows)
    return go.Scattermap(lat=lats, lon=lons, mode="markers", name="Salmon site",
                         marker=dict(size=12, color=SITE_COLOR, opacity=0.9),
                         customdata=keys, text=[f"{n}<br>{l}" for n, l in zip(names, labels)],
                         hovertemplate="%{text}<br><i>click to show this run</i><extra></extra>")


def _finish_map(fig, df, height=600, bottom=0):
    center, zoom = map_view(df)
    fig.update_layout(map=dict(style="carto-positron", center=center, zoom=zoom),
                      margin=dict(l=0, r=0, t=0, b=bottom), height=height, uirevision=str(center),
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),
                      font=dict(family=FONT, size=12, color=INK))
    return fig


def sightings_map_year(df, sources):
    """All year: sightings coloured by month; candidates smaller and fainter."""
    fig = go.Figure()
    for status, size, opacity in [("Confirmed", 8, 0.8), ("Candidate", 6, 0.35)]:
        s = df[df["status"] == status]
        if s.empty:
            continue
        fig.add_trace(go.Scattermap(
            lat=s["latitude"], lon=s["longitude"], mode="markers",
            name="Confirmed sighting" if status == "Confirmed" else "Candidate (unconfirmed)",
            marker=dict(size=size, opacity=opacity, color=s["month"] - 1, cmin=0, cmax=11,
                        colorscale=MONTH_SCALE, showscale=(status == "Confirmed"),
                        colorbar=dict(title="Month", tickvals=list(range(12)), ticktext=MONTHS,
                                      thickness=12, len=0.85)),
            text=s["label"], hovertemplate="%{text}<extra></extra>"))
    fig.add_trace(_site_trace(sources))
    return _finish_map(fig, df)


def sightings_map_monthly(df, sources, density_max=6):
    """By month: one frame per month with confirmed sightings over a density
    layer. The density colour scale is fixed (density_max) so a quiet month
    looks quiet instead of being rescaled to look as busy as a busy one."""
    density_scale = [[0, "rgba(253,231,37,0)"], [0.2, "rgba(53,183,121,0.35)"], [1, "rgba(68,1,84,0.75)"]]
    sites = _site_trace(sources)

    def month_traces(m):
        s = df[(df["month"] == m) & (df["status"] == "Confirmed")]
        c = df[(df["month"] == m) & (df["status"] == "Candidate")]
        return [
            go.Densitymap(lat=s["latitude"], lon=s["longitude"], radius=14, zmin=0, zmax=density_max,
                          colorscale=density_scale, showscale=False, name="Density", hoverinfo="skip"),
            go.Scattermap(lat=s["latitude"], lon=s["longitude"], mode="markers", name="Confirmed sighting",
                          marker=dict(size=7, color="#3e4989", opacity=0.8),
                          text=s["label"], hovertemplate="%{text}<extra></extra>"),
            go.Scattermap(lat=c["latitude"], lon=c["longitude"], mode="markers",
                          name="Candidate (unconfirmed)", marker=dict(size=5, color="#888780", opacity=0.5),
                          text=c["label"], hovertemplate="%{text}<extra></extra>"),
            sites,
        ]

    counts = df[df["status"] == "Confirmed"].groupby("month").size()
    frames = [go.Frame(data=month_traces(m), name=MONTHS[m - 1]) for m in range(1, 13)]
    fig = go.Figure(data=month_traces(1), frames=frames)
    steps = [dict(method="animate", label=f"{MONTHS[m - 1]} ({counts.get(m, 0)})",
                  args=[[MONTHS[m - 1]], dict(mode="immediate", frame=dict(duration=0, redraw=True))])
             for m in range(1, 13)]
    fig.update_layout(
        # the slider spans the full width; Play/Pause sit on their own row below
        # it, so they never cover the first month labels on a narrow screen
        sliders=[dict(steps=steps, x=0, len=1, y=0, yanchor="top", pad=dict(t=10, l=28, r=28),
                      currentvalue=dict(prefix="Month (confirmed sightings): ", xanchor="right"))],
        updatemenus=[dict(type="buttons", direction="left", x=0, y=0, xanchor="left", yanchor="top",
                          pad=dict(r=6, t=100), showactive=False,
                          buttons=[dict(label="▶ Play", method="animate",
                                        args=[None, dict(frame=dict(duration=900, redraw=True),
                                                         fromcurrent=True, mode="immediate")]),
                                   dict(label="❚❚ Pause", method="animate",
                                        args=[[None], dict(frame=dict(duration=0, redraw=False),
                                                           mode="immediate", transition=dict(duration=0))])])])
    return _finish_map(fig, df, height=600, bottom=150)


# ---- Run timing over the years -------------------------------------------------
def run_timing(sources, selected_keys, pod="All pods", highlight_year=None):
    """Date by which half of each run (or half of the year's central Salish
    Sea orca sighting days) had passed, by year. Orca series: shaded band for
    the 25-75% dates; hollow points where candidate sightings change the value."""
    fig = go.Figure()
    if "srkw" in selected_keys:
        conf = sighting_timing(pod)
        fig.add_trace(go.Scatter(x=conf["year"], y=conf["q25"], mode="lines", line=dict(width=0),
                                 hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=conf["year"], y=conf["q75"], mode="lines", line=dict(width=0),
                                 fill="tonexty", fillcolor="rgba(98,80,214,0.13)", hoverinfo="skip",
                                 name="Orca 25-75% of sighting days"))
        color, dash = TIMING_STYLE["srkw"]
        fig.add_trace(go.Scatter(x=conf["year"], y=conf["q50"], mode="lines+markers",
                                 name="Orca sighting days (central Salish Sea)",
                                 line=dict(color=color, dash=dash, width=2), marker=dict(size=6),
                                 customdata=[doy_label(d) for d in conf["q50"]],
                                 hovertemplate="%{customdata}"))
        if pod == "All pods":
            cand = sighting_timing(pod, include_candidates=True).merge(conf, on="year", suffixes=("", "_c"))
            cand = cand[cand["q50"] != cand["q50_c"]]
            if len(cand):
                fig.add_trace(go.Scatter(x=cand["year"], y=cand["q50"], mode="markers",
                                         name="Orca, including candidate sightings",
                                         marker=dict(size=10, color="rgba(0,0,0,0)", line=dict(color=color, width=2)),
                                         customdata=[doy_label(d) for d in cand["q50"]],
                                         hovertemplate="%{customdata}"))
    for s in sources:
        if s.key not in selected_keys:
            continue
        t = s.timing
        color, dash = TIMING_STYLE.get(s.key, ("#888", "solid"))
        fig.add_trace(go.Scatter(x=t["year"], y=t["q50"], mode="lines+markers", name=s.label,
                                 line=dict(color=color, dash=dash, width=2), marker=dict(size=5),
                                 customdata=[doy_label(d) for d in t["q50"]],
                                 hovertemplate="%{customdata}"))
    if highlight_year:
        fig.add_vline(x=highlight_year, line=dict(color="#bbb", width=1, dash="dot"))
    ticks = list(range(1, 366, 30))
    fig.update_yaxes(tickvals=ticks, ticktext=[doy_label(d) for d in ticks], title_text="Halfway date")
    # start at 1980, when the Albion record begins (Bonneville goes back to 1939)
    fig.update_xaxes(title_text="Year", dtick=5, range=[1979.5, CURYR + 0.5])
    return _base_layout(fig, height=480)
