"""The one-page layout. Rows, top to bottom: header with the year and pod
menus, status cards, map + salmon monitor, run timing, notes and sources.
assets/onepage.css stacks the rows on phones and puts the map and the salmon
monitor side by side on wider screens."""
from dash import dcc, html

from .config import CURYR, NORMAL_YEARS
from .salmon import SALMON_SOURCES, TIMING_SOURCES
from .sightings import PODS, sighting_years

ALBION_V_BONNEVILLE = "albion-v-bonneville"

INTRO = ("Southern Resident killer whales depend on Chinook salmon, and the decline of Chinook "
         "is a major reason the population is struggling. This dashboard puts this year's salmon "
         "runs next to where and when the whales were reported.")

NOTES = f"""
**% of normal** compares this year's total from January 1 to today's date with the average
of up to the {NORMAL_YEARS} previous years, each cut at the same date (for a past year, the
whole year is compared). For test fisheries (Albion) it compares catch per unit of effort, an
index of how well the net caught fish, not a count of fish.

**Candidate sightings.** In March 2026 Acartia stopped labelling most reports
"Southern Resident" and began typing them only as "Orca". Reports typed "Orca" with no sign
of Bigg's killer whales are shown as *candidate (unconfirmed)* sightings, separately from
confirmed ones. Earlier years have no candidates because the labels were still in use. Some
candidates are probably unlabelled Bigg's killer whales.

**Where whales were reported, not a survey.** Sightings cluster where people are watching:
ferry routes, shorelines, whale-watch boats and hydrophone networks, so busy viewing areas can
look like hotspots. To reduce this, the charts count sighting *days* rather than reports.

**Central Salish Sea** means north of the entrance to Puget Sound (latitude 48.19°N), following
Monika Weiland's definition in her talk on Southern Resident and Bigg's occupancy metrics. The
orca bars and run-timing series use central Salish Sea sightings; the map shows all of them.

**Run timing** shows the date by which half of each year's run had passed the counting site
(for orcas, half of the year's sighting days). Fish are counted after they pass the whales'
feeding areas, so a counting date is a little later than when the fish were available to the
whales. Bonneville's spring, summer and fall runs are split by DART's date ranges.
"""

ORCA_SOURCES = ("Orca sightings are from [Acartia](https://acartia.io/home) (2018-present) and "
                "[The Whale Museum](https://whalemuseum.org/) (1990-2021).")


def _menu(label, component):
    return html.Div(className="menu", children=[html.Label(label), component])


def header(app):
    # every year with sightings or salmon data, newest first (a public copy
    # of the code may have salmon data only)
    years = sorted(set(sighting_years()) | {y for s in SALMON_SOURCES for y in s.years()}, reverse=True)
    return html.Header(className="page-header", children=[
        html.Div(className="title-block", children=[
            # Official Orcasound wordmarks (transparent SVG): Deep Blue on the
            # light page, white on the dark page; CSS shows the one that matches
            html.A([html.Img(src=app.get_asset_url("orcasound-wordmark-deepblue.svg"),
                             className="logo logo-light", alt="Orcasound"),
                    html.Img(src=app.get_asset_url("orcasound-wordmark-white.svg"),
                             className="logo logo-dark", alt="Orcasound")],
                   href="https://www.orcasound.net/", target="_blank", className="logo-link"),
            html.H1("Chinook and orca"),
            html.P("Are the salmon runs where and when the whales are?", className="subtitle"),
        ]),
        html.Div(className="menus", children=[
            _menu("Year", dcc.Dropdown(id="year", options=years, value=CURYR if CURYR in years else years[0],
                                       clearable=False)),
            _menu("Orcas", dcc.Dropdown(id="pod", options=PODS, value="All pods", clearable=False)),
            html.Button("☾", id="theme-toggle", className="theme-toggle", n_clicks=0,
                        title="Switch between light and dark", **{"aria-label": "Switch between light and dark"}),
            html.A(html.Img(src=app.get_asset_url("icone-github-grise.png"), className="github"),
                   href="https://github.com/liu-zoe/orcasalmon", target="_blank"),
        ]),
    ])


def build_layout(app):
    # Albion vs Bonneville first, then Albion and Bonneville, then the rest
    first = ["albion-chinook", "bonneville"]
    ordered = ([s for k in first for s in SALMON_SOURCES if s.key == k]
               + [s for s in SALMON_SOURCES if s.key not in first])
    location_options = ([{"label": "Albion vs Bonneville", "value": ALBION_V_BONNEVILLE}]
                        + [{"label": s.label, "value": s.key} for s in ordered])
    timing_options = ([{"label": "Orca sighting days", "value": "srkw"}]
                      + [{"label": s.label, "value": s.key} for s in TIMING_SOURCES])
    default_timing = ["srkw", "albion-chinook", "bonneville-fall", "lake-washington",
                      "ps-hatcheries", "albion-chum"]
    return html.Div(className="page", children=[
        dcc.Store(id="theme", storage_type="local", data="light"),  # remembered in the browser
        header(app),
        html.P(INTRO, className="intro"),

        html.Section(className="row", children=[
            html.Div(id="cards-caption", className="caption"),
            html.Div(id="cards", className="cards"),
        ]),

        html.Section(className="row two-up", children=[
            html.Div(className="panel", children=[
                html.H2("Southern Resident sightings"),
                dcc.RadioItems(id="map-view", options=["All year", "By month"], value="All year",
                               inline=True, className="radio"),
                dcc.Graph(id="sightings-map", config={"displaylogo": False}, style={"height": "600px"}),
                html.P("Map shows where whales were reported, not a survey of where they were. "
                       "Click an orange salmon site to show its run.", className="note"),
            ]),
            html.Div(className="panel", children=[
                html.H2("Salmon monitor"),
                dcc.Dropdown(id="location", options=location_options, value=ALBION_V_BONNEVILLE,
                             clearable=False),
                dcc.Graph(id="salmon-monitor", config={"displaylogo": False}, style={"height": "520px"}),
                html.P("Bars: days each week with a Southern Resident sighting in the central Salish "
                       "Sea (lighter: candidate sightings only). Lines: the selected year and the two "
                       "before it, against the average of all earlier years.", className="note"),
            ]),
        ]),

        html.Section(className="row panel", children=[
            html.H2("Run timing over the years"),
            dcc.Checklist(id="timing-series", options=timing_options, value=default_timing,
                          inline=True, className="checklist"),
            dcc.Graph(id="run-timing", config={"displaylogo": False}, style={"height": "480px"}),
        ]),

        html.Section(className="row notes", children=[
            html.H2("Notes"),
            dcc.Markdown(NOTES),
            html.H2("Data sources"),
            dcc.Markdown("\n\n".join([f"- {s.description}" for s in SALMON_SOURCES if s.description]
                                     + [f"- {ORCA_SOURCES}"])),
        ]),
    ])
