"""Dash callbacks: connect the menus to the cards and charts."""
from datetime import date

import numpy as np
from dash import ALL, Input, Output, State, ctx, html, no_update

from . import charts
from .config import CURYR, NORMAL_YEARS, TODAY
from .layout import ALBION_V_BONNEVILLE
from .salmon import SALMON_SOURCES, SOURCES_BY_KEY, TIMING_SOURCES
from .sightings import load_sightings, sighting_days_to_date, sighting_years


def _through(year):
    """Cut-off date for 'to date' figures: today for the current year,
    the whole year for past years."""
    return TODAY if year == CURYR else date(year, 12, 31)


def _card(key, title, value, detail):
    return html.Button(className="card", id={"type": "card", "key": key}, n_clicks=0, children=[
        html.Div(title, className="card-title"),
        html.Div(value, className="card-value"),
        html.Div(detail, className="card-detail"),
    ])


def salmon_card(source, year):
    pct, normal_years = source.percent_of_normal(year, _through(year))
    if pct is None:
        return _card(source.key, source.label, "–", "no data for this period")
    span = f"{normal_years[0]}–{normal_years[-1]}" if len(normal_years) > 1 else str(normal_years[0])
    return _card(source.key, source.label, f"{pct:.0f}%", f"of normal ({span} average)")


def orca_card(year, pod):
    if not sighting_years():  # no sightings data in this copy
        return html.Div(className="card orca", children=[
            html.Div("Orca sighting days (central Salish Sea)", className="card-title"),
            html.Div("–", className="card-value"),
            html.Div("no sightings data (run scraper.py)", className="card-detail"),
        ])
    through = _through(year)
    conf, cand = sighting_days_to_date(year, through, pod)
    earlier = [y for y in sighting_years() if y < year][:NORMAL_YEARS]
    normal = np.mean([sighting_days_to_date(y, through, pod)[0] for y in earlier]) if earlier else None
    value = f"{conf} + {cand}" if cand else str(conf)
    detail = ("confirmed + candidate days" if cand else "sighting days") + (
        f" · normal {normal:.0f}" if normal is not None else "")
    return html.Div(className="card orca", children=[
        html.Div("Orca sighting days (central Salish Sea)", className="card-title"),
        html.Div(value, className="card-value"),
        html.Div(detail, className="card-detail"),
    ])


def register(app):
    # ---- Light / dark theme -------------------------------------------------
    @app.callback(Output("theme", "data"), Input("theme-toggle", "n_clicks"),
                  State("theme", "data"), prevent_initial_call=True)
    def toggle_theme(_n, theme):
        return "light" if theme == "dark" else "dark"

    # Runs in the browser: sets <html data-theme="..."> for the CSS, and shows
    # the icon of the theme you'd switch to (moon in light mode, sun in dark).
    app.clientside_callback(
        """function (theme) {
            document.documentElement.dataset.theme = theme || "light";
            return theme === "dark" ? "\u2600\ufe0e" : "\u263e";
        }""",
        Output("theme-toggle", "children"), Input("theme", "data"))

    @app.callback(Output("cards", "children"), Output("cards-caption", "children"),
                  Input("year", "value"), Input("pod", "value"))
    def update_cards(year, pod):
        through = _through(year)
        caption = (f"{year} so far, January 1 to {through:%B %-d}, compared with normal"
                   if year == CURYR else f"{year}, whole year, compared with normal")
        return [salmon_card(s, year) for s in SALMON_SOURCES if s.in_menu] + [orca_card(year, pod)], caption

    @app.callback(Output("sightings-map", "figure"),
                  Input("year", "value"), Input("pod", "value"), Input("map-view", "value"),
                  Input("theme", "data"))
    def update_map(year, pod, view, theme):
        df = load_sightings(year, pod)
        sources = [s for s in SALMON_SOURCES if s.in_menu]
        if view == "By month":
            fig = charts.sightings_map_monthly(df, sources)
        else:
            fig = charts.sightings_map_year(df, sources)
        return charts.apply_theme(fig, theme)

    @app.callback(Output("location", "value"),
                  Input("sightings-map", "clickData"),
                  Input({"type": "card", "key": ALL}, "n_clicks"),
                  prevent_initial_call=True)
    def pick_location(click, _card_clicks):
        """Clicking a salmon site on the map, or a salmon card, shows that run."""
        trig = ctx.triggered_id
        if trig == "sightings-map":
            point = (click or {}).get("points", [{}])[0]
            key = point.get("customdata")
            return key if key in SOURCES_BY_KEY else no_update
        if isinstance(trig, dict) and ctx.triggered[0]["value"]:
            return trig["key"]
        return no_update

    @app.callback(Output("salmon-monitor", "figure"),
                  Input("location", "value"), Input("year", "value"), Input("pod", "value"),
                  Input("theme", "data"))
    def update_monitor(location, year, pod, theme):
        if location == ALBION_V_BONNEVILLE:
            fig = charts.albion_vs_bonneville(year, pod)
        else:
            fig = charts.salmon_monitor(SOURCES_BY_KEY[location], year, pod)
        return charts.apply_theme(fig, theme)

    @app.callback(Output("run-timing", "figure"),
                  Input("timing-series", "value"), Input("pod", "value"), Input("year", "value"),
                  Input("theme", "data"))
    def update_timing(selected, pod, year, theme):
        fig = charts.run_timing(TIMING_SOURCES, selected or [], pod, highlight_year=year)
        return charts.apply_theme(fig, theme)
