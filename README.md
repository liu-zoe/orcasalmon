# Orca Salmon Dashboard

### Link
https://salmonorca.fly.dev

## __Project Description__
A one-page dashboard comparing Chinook salmon runs (Fraser River at Albion, BC; Columbia River at Bonneville Dam; Lake Washington; Puget Sound hatcheries) and fall chum and coho with Southern Resident killer whale sightings in and around the Salish Sea: status cards ("% of normal"), a sightings map, a salmon monitor and run timing over the years.

### Data in this repository
This repository includes the **salmon data** (`data/foschinook`, `foschum`, `foscoho`, `bonchinook`, `lakewash`, `pshatchery`), so the salmon charts work right after cloning. It does **not** include orca sightings:
- **Acartia** sightings (`data/acartia/`) are downloaded with `python scraper.py`, which needs your own Acartia API token in `acartia_token.txt` (or the `ACARTIA_TOKEN` environment variable).
- **The Whale Museum** sightings archive (1990–2021) is not public and is not included.

Without sightings data the dashboard still runs; the orca card, map and orca series are simply empty.

### Running it
```bash
pip install -r requirements.txt
python app.py          # dashboard at http://127.0.0.1:8050
python scraper.py      # download this year's salmon and orca data into data/
```
Deployment runs `gunicorn app:server` (see `Procfile`).

### Weekly data update
```bash
python scraper.py                                            # downloads this year's data
git status --short data/                                     # which files changed
git diff --stat data/                                        # how much each changed
git restore data/<folder>/<file>.csv                         # undo any file that looks wrong
git add data/ && git commit -m "data update"                 # keep the rest
```
- A download with **fewer rows** than the saved file (for example an empty DFO report) is not written; the scraper prints `! Kept existing ...` instead. If a source really did revise its data downward, rerun it with `force=True`, e.g. `from orcasalmon.salmon import albion_chinook; albion_chinook.download(2026, force=True)`.
- The raw Acartia snapshot `data/acartia/acartia_<date>.csv` is git-ignored; only `srkw_<year>.csv` is committed.
- Lake Washington has no automatic download: after each season, save WDFW's table to `data/lakewash/<year>.csv` (see [data/lakewash/README.md](data/lakewash/README.md)).

### Code layout
| File | What it does |
|---|---|
| `app.py` | Creates the Dash app and exposes `server` for gunicorn |
| `scraper.py` | Weekly data download: every salmon source, then Acartia |
| `orcasalmon/config.py` | Paths, dates and constants |
| `orcasalmon/salmon.py` | `SalmonSource` classes: download and load each salmon source; `SALMON_SOURCES` lists the ones on the page |
| `orcasalmon/sightings.py` | `SightingSource` classes for The Whale Museum and Acartia, pod/region filters, sighting days and timing |
| `orcasalmon/acartia.py` | Acartia download and Southern Resident tagging |
| `orcasalmon/charts.py` | Plotly figures |
| `orcasalmon/layout.py`, `orcasalmon/callbacks.py` | The page and its interactivity |
| `assets/onepage.css` | Responsive styles (stacks on phones) |

To add a salmon source, write or reuse a `SalmonSource` subclass in `orcasalmon/salmon.py` and add it to `SALMON_SOURCES`; the menu, map marker, status card, footer text and weekly download pick it up automatically.

### **Data**
#### Salmon Data
1. Albion Chinook test fishery is located on the lower Fraser River at Albion, BC (near Fort Langley), Canada. The fishery collects data from early April to mid-October every year. Catching per unit effort, or CPUE, is defined as catch per thousand fathom minutes. Data is retrieved from the Fisheries and Oceans Canada [report website](https://www-ops2.pac.dfo-mpo.gc.ca/fos2_Internet/Testfish/rptcsbdparm.cfm?stat=CPTFM&fsub_id=242). Read more about the Albion Chinook gill net data set, such as what size of net is used, in this document on [Albion Chinook Gillnet](https://www.pac.dfo-mpo.gc.ca/fm-gp/fraser/docs/commercial/albionchinook-quinnat-eng.html). 

2. Bonneville Dam data is retrieved from Columbia Basin Research [Adult Passage Queries](https://www.cbr.washington.edu/dart/query/adult_daily). Number of adult Chinook salmon passing through the Bonneville Dam was directly monitored April to October, with video monitoring covering the other months. See [Fish Passage Center](https://www.fpc.org/adults/Q_adults_subsite.php) for more details. 

3. Lake Washington data is the daily count of adult Chinook salmon passing through the Hiram M. Chittenden (Ballard) Locks in Seattle, retrieved from the Washington Department of Fish and Wildlife [Lake Washington salmon counts](https://wdfw.wa.gov/fishing/reports/counts/lake-washington). WDFW and the Muckleshoot Indian Tribe count the fish cooperatively from late June to early October. WDFW's page only shows the current season, so each year is saved to `data/lakewash/YYYY.csv` once its season ends (past seasons were recovered from Wayback Machine copies; see [data/lakewash/README.md](data/lakewash/README.md) for the snapshot used for each year). Counts are preliminary and subject to revision.

4. Puget Sound hatchery data is the weekly total of adult and jack Chinook arriving at the traps of Soos Creek (Green River), Issaquah (Lake Washington), Voights Creek (Puyallup River) and Wallace River (Skykomish River) hatcheries, 1997 to present. It comes from the "Trap Estimate" records of the WDFW [Hatchery Adult Salmon Returns](https://data.wa.gov/Natural-Resources-Environment/WDFW-Hatchery-Adult-Salmon-Returns/9q4e-xhag) dataset on data.wa.gov (Socrata API), saved to `data/pshatchery/hatchery_chinook.csv`. Counts are rounded estimates on irregular dates, and fish reach the hatcheries weeks after passing through Puget Sound.

5. Albion chum and coho data comes from the Fisheries and Oceans Canada Albion chum gillnet test fishery (`fsub_id=227`) on the lower Fraser, 1988 to present, saved to `data/foschum/` and `data/foscoho/`. It fishes every other day from September 1 to October 20 and daily to the end of November. Chum and coho become a larger share of the Southern Resident diet in the fall as Chinook decline.

#### Orca Data
1. Orca sightings data is retrieved from [Acartia](https://acartia.io/home) and [The Whale Museum](https://whalemuseum.org). 

### Author
> [Zoe Liu](https://github.com/liu-zoe)
