"""Salmon data sources.

Every source is an object built from a SalmonSource subclass. A subclass knows
two things about its source:

* how to download one year of data into data/<folder>/      -> download(year)
* how to read one year of saved data as (date, value) rows  -> read_year(year)

Everything else (combining years, day-of-year tables for charts, run timing,
"% of normal") is written once in the SalmonSource base class and shared.

To add a new source, write a subclass (or reuse one, e.g. another DFO test
fishery is just another FOSTestFishery(...)) and add it to SALMON_SOURCES.
"""
import html as htmlmod
import os
import re
from datetime import date
from functools import cached_property

import numpy as np
import pandas as pd
import requests

from .config import DATA_DIR, NORMAL_YEARS, REFERENCE_YEAR


class SalmonSource:
    """Base class: one salmon data source (a counting site or a test fishery).

    Parameters shared by all sources
    --------------------------------
    key          short id used in menus and callbacks, e.g. "albion-chinook"
    label        name shown on the page, e.g. "Albion Chinook (Fraser)"
    folder       sub-folder of data/ holding the saved files
    units        y-axis label: "CPUE" or "Count"
    region       "Fraser", "Columbia" or "Puget Sound" (for grouping)
    sites        list of (name, latitude, longitude) for the map markers
    description  markdown for the data-sources footer
    window       optional (start "MM-DD", end "MM-DD"): keep only these dates
                 every year (used to split Bonneville into spring/summer/fall)
    in_menu      show in the salmon-monitor menu and status cards
    in_timing    offer in the run-timing chart
    hist_digits  rounding of the historical mean line
    fill_gaps    when averaging past years, fill days skipped within a season
                 (for every-other-day fishing schedules)
    weekly       chart this source as weekly totals instead of daily values
    lead_days    rough days between fish passing the whales' feeding areas and
                 being counted here; recorded for later, not applied yet
    """

    def __init__(self, key, label, folder, units, region, sites, description,
                 window=None, in_menu=True, in_timing=True, hist_digits=2,
                 fill_gaps=False, weekly=False, lead_days=None):
        self.key = key
        self.label = label
        self.folder = DATA_DIR / folder
        self.units = units
        self.region = region
        self.sites = sites
        self.description = description
        self.window = window
        self.in_menu = in_menu
        self.in_timing = in_timing
        self.hist_digits = hist_digits
        self.fill_gaps = fill_gaps
        self.weekly = weekly
        self.lead_days = lead_days

    def __repr__(self):
        return f"{type(self).__name__}({self.key!r})"

    # ---- To be written by each subclass -------------------------------------
    def years(self):
        """Years with a saved data file."""
        raise NotImplementedError

    def read_year(self, year):
        """Return a DataFrame with columns 'date' (Timestamp) and 'value'."""
        raise NotImplementedError

    def download(self, year):
        """Download one year of data into self.folder."""
        raise NotImplementedError(
            f"{self.label} has no automatic download; see data/{self.folder.name}/")

    @property
    def can_download(self):
        return type(self).download is not SalmonSource.download

    def _save(self, path, write, new_rows, old_rows, force=False):
        """Write a freshly downloaded file, unless it has fewer data rows than
        the file already saved (e.g. the DFO site sometimes returns an empty
        report). Then keep the old file and say so; force=True overrides.
        `write` is a function that writes the new file. Returns True if saved."""
        if not force and path.exists() and new_rows < old_rows:
            print(f"  ! Kept existing {path.relative_to(DATA_DIR)}: the download has {new_rows} "
                  f"rows but the saved file has {old_rows}. Use download(..., force=True) to replace it.")
            return False
        os.makedirs(path.parent, exist_ok=True)
        write()
        print(f"  saved {path.relative_to(DATA_DIR)} ({new_rows} rows)")
        return True

    # ---- Shared behaviour ---------------------------------------------------
    @cached_property
    def daily(self):
        """All years in one long table: date, value, year, month, day, doy."""
        frames = [self.read_year(y) for y in self.years()]
        df = pd.concat([f for f in frames if len(f)], ignore_index=True)
        df = df.dropna(subset=["date"]).sort_values("date")
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        df["day"] = df["date"].dt.day
        df["doy"] = df["date"].dt.dayofyear
        if self.window:
            mmdd = df["date"].dt.strftime("%m-%d")
            df = df[(mmdd >= self.window[0]) & (mmdd <= self.window[1])]
        return df.reset_index(drop=True)

    @cached_property
    def by_day(self):
        """Wide table for charts: one row per calendar day (or week), one
        column per year named v<YYYY>, plus 'x', the day placed in
        REFERENCE_YEAR so all years share one date axis."""
        d = self.daily
        if self.weekly:
            d = d.assign(week=(d["doy"] - 1) // 7)
            wide = d.pivot_table(index="week", columns="year", values="value", aggfunc="sum")
            wide = wide.reindex(range(wide.index.min(), wide.index.max() + 1))
            # a week with no count inside a year's season means none counted
            for c in wide.columns:
                last = wide[c].last_valid_index()
                wide.loc[:last, c] = wide.loc[:last, c].fillna(0)
            wide.columns = [f"v{c}" for c in wide.columns]
            wide = wide.reset_index()
            wide["x"] = pd.Timestamp(REFERENCE_YEAR, 1, 1) + pd.to_timedelta(wide["week"] * 7, unit="D")
            return wide
        # min_count=1 keeps a day with no count blank instead of 0
        wide = d.groupby(["month", "day", "year"])["value"].sum(min_count=1).unstack("year")
        wide.columns = [f"v{c}" for c in wide.columns]
        wide = wide.reset_index()
        wide["x"] = pd.to_datetime(dict(year=REFERENCE_YEAR, month=wide["month"], day=wide["day"]))
        return wide.sort_values("x").reset_index(drop=True)

    def history_mean(self, years):
        """Mean of the given years, day by day, for the 'historical mean' line."""
        cols = [f"v{y}" for y in years if f"v{y}" in self.by_day]
        if not cols:
            return None
        hist = self.by_day[cols]
        if self.fill_gaps:
            hist = hist.interpolate(limit_area="inside")
        return hist.mean(axis=1, skipna=True).round(self.hist_digits)

    def total_to_date(self, year, through):
        """Sum of values in `year` from Jan 1 through the month/day of `through`."""
        d = self.daily
        d = d[d["year"] == year]
        md = d["month"] * 100 + d["day"]
        return float(d.loc[md <= through.month * 100 + through.day, "value"].sum())

    def percent_of_normal(self, year, through):
        """This year's total to date as a percent of the average of up to
        NORMAL_YEARS earlier years, each cut at the same month/day.
        Returns (percent or None, list of years used as normal)."""
        earlier = [y for y in self.years() if y < year and y in set(self.daily["year"])]
        normal_years = earlier[-NORMAL_YEARS:]
        if not normal_years or year not in set(self.daily["year"]):
            return None, normal_years
        normal = np.mean([self.total_to_date(y, through) for y in normal_years])
        if normal == 0:
            return None, normal_years
        return 100 * self.total_to_date(year, through) / normal, normal_years

    @cached_property
    def timing(self):
        """Run timing by year: day of year by which 25%, 50% and 75% of that
        year's total had passed. Columns: year, q25, q50, q75."""
        rows = []
        for y, g in self.daily.groupby("year"):
            g = g.sort_values("doy")
            total = g["value"].fillna(0).sum()
            if total <= 0:
                continue
            share = g["value"].fillna(0).cumsum() / total
            rows.append([y] + [int(g.loc[share >= q, "doy"].iloc[0]) for q in (0.25, 0.5, 0.75)])
        return pd.DataFrame(rows, columns=["year", "q25", "q50", "q75"])


# ---------------------------------------------------------------------------
# DFO Fishery Operations System test fisheries (Albion Chinook, chum, coho)
# ---------------------------------------------------------------------------
FOS_REPORT_URL = "https://www-ops2.pac.dfo-mpo.gc.ca/fos2_Internet/Testfish/rptCSbD.cfm?stat=CPTFM"
FOS_SPECIES_CODES = {"CHINOOK": 124, "CHUM": 112, "COHO": 115, "PINK": 108, "SOCKEYE": 118}
FOS_COLUMNS = ["day", "mon", "year", "netlen", "catch1", "sets1", "effort1", "cpue1",
               "catch2", "sets2", "effort2", "cpue2"]


class FOSTestFishery(SalmonSource):
    """A DFO test fishery. Files: fosYYYY.csv with daily CPUE (vessel 1).
    fsub_id picks the fishery on DFO's report site; species picks the fish."""

    def __init__(self, key, label, folder, fsub_id, species, **kwargs):
        super().__init__(key, label, folder, **kwargs)
        self.fsub_id = fsub_id
        self.species = species

    def years(self):
        return sorted(int(f[3:7]) for f in os.listdir(self.folder)
                      if re.fullmatch(r"fos\d{4}\.csv", f))

    def read_year(self, year):
        d = pd.read_csv(self.folder / f"fos{year}.csv", usecols=["day", "mon", "cpue1"])
        dates = pd.to_datetime(d["day"].astype(int).astype(str) + " " + d["mon"] + f" {year}",
                               format="%d %b %Y", errors="coerce")
        return pd.DataFrame({"date": dates, "value": d["cpue1"]})

    def download(self, year, force=False):
        """Fetch DFO's catch summary report with a plain HTTP POST and save
        the daily rows (same columns as the older Selenium scraper)."""
        r = requests.post(FOS_REPORT_URL, timeout=120, data={
            "lboYears": str(year), "lboFsub": self.fsub_id,
            "lboSpecies": FOS_SPECIES_CODES[self.species], "cmdRunReport": "Run Report"})
        r.raise_for_status()
        rows = []
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", r.text, flags=re.S | re.I):
            cells = [htmlmod.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                     for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, flags=re.S | re.I)]
            # daily rows: "01 Sep 2025", net length, then 4 values per vessel
            if len(cells) == 10 and re.fullmatch(r"\d{2} [A-Za-z]{3} \d{4}", cells[0]):
                rows.append(cells[0].split(" ") + cells[1:])
        path = self.folder / f"fos{year}.csv"
        old_rows = len(pd.read_csv(path)) if path.exists() else 0
        new = pd.DataFrame(rows, columns=FOS_COLUMNS)
        return self._save(path, lambda: new.to_csv(path, index=False), len(new), old_rows, force)


# ---------------------------------------------------------------------------
# Columbia Basin Research DART adult counts (Bonneville Dam)
# ---------------------------------------------------------------------------
DART_CSV_URL = "https://www.cbr.washington.edu/dart/cs/php/rpt/adult_daily.php"


class DartAdultCounts(SalmonSource):
    """Daily adult Chinook counts at a Columbia River dam. Files: bonYYYY.csv
    as downloaded from DART (all species; we keep the 'Chin' column)."""

    def __init__(self, key, label, folder, project="BON", project_name="Bonneville", **kwargs):
        super().__init__(key, label, folder, **kwargs)
        self.project = project
        self.project_name = project_name

    def years(self):
        return sorted(int(f[3:7]) for f in os.listdir(self.folder)
                      if re.fullmatch(r"bon\d{4}\.csv", f))

    def read_year(self, year):
        d = pd.read_csv(self.folder / f"bon{year}.csv", usecols=["Project", "Date", "Chin"])
        d = d[d["Project"] == self.project_name]
        return pd.DataFrame({"date": pd.to_datetime(d["Date"], errors="coerce"),
                             "value": d["Chin"].clip(lower=0)})

    def _count_rows(self, csv_text_or_path):
        """Days with a Chinook count for this dam in a DART CSV."""
        import io
        src = io.StringIO(csv_text_or_path) if isinstance(csv_text_or_path, str) else csv_text_or_path
        try:
            d = pd.read_csv(src, usecols=["Project", "Chin"])
        except (ValueError, pd.errors.ParserError, pd.errors.EmptyDataError):
            return 0
        return int(((d["Project"] == self.project_name) & d["Chin"].notna()).sum())

    def download(self, year, force=False):
        """DART serves the query result directly as CSV (no browser needed)."""
        r = requests.get(DART_CSV_URL, timeout=120, params={
            "sc": 1, "outputFormat": "csv", "year": year, "proj": self.project,
            "span": "no", "startdate": "1/1", "enddate": "12/31", "run": ""})
        r.raise_for_status()
        path = self.folder / f"bon{year}.csv"
        old_rows = self._count_rows(path) if path.exists() else 0
        return self._save(path, lambda: path.write_text(r.text), self._count_rows(r.text), old_rows, force)


# ---------------------------------------------------------------------------
# WDFW Lake Washington (Ballard Locks) daily Chinook counts
# ---------------------------------------------------------------------------
class WDFWLakeWashington(SalmonSource):
    """Daily Chinook counts at the Ballard Locks. Files: YYYY.csv with columns
    Date (M/D), Daily Count, Running Total. WDFW's page shows only the current
    season, so files are saved by hand after each season (no download())."""

    def years(self):
        return sorted(int(f[:4]) for f in os.listdir(self.folder) if re.fullmatch(r"\d{4}\.csv", f))

    def read_year(self, year):
        d = pd.read_csv(self.folder / f"{year}.csv", usecols=["Date", "Daily Count"])
        # WDFW sometimes lists a date range ("6/18-6/30"); use its end date
        md = d["Date"].astype(str).str.split("-").str[-1]
        dates = pd.to_datetime(md + f"/{year}", format="%m/%d/%Y", errors="coerce")
        return pd.DataFrame({"date": dates, "value": d["Daily Count"]})


# ---------------------------------------------------------------------------
# WDFW hatchery adult returns (data.wa.gov, Socrata API)
# ---------------------------------------------------------------------------
HATCHERY_URL = "https://data.wa.gov/resource/9q4e-xhag.csv"


class WDFWHatcheryReturns(SalmonSource):
    """Chinook 'Trap Estimate' events at WDFW hatcheries, from one file
    (hatchery_chinook.csv) that holds every year. Each row is the number of
    fish counted at a trap on one date; adults and jacks are added together."""

    def __init__(self, key, label, folder, facilities, filename="hatchery_chinook.csv", **kwargs):
        super().__init__(key, label, folder, **kwargs)
        self.facilities = facilities
        self.filename = filename

    @cached_property
    def _all(self):
        d = pd.read_csv(self.folder / self.filename, parse_dates=["date"])
        d = d[d["facility"].isin(self.facilities)]
        d["value"] = d["adult_count"].fillna(0) + d["jack_count"].fillna(0)
        return d

    def years(self):
        return sorted(self._all["date"].dt.year.unique().tolist())

    def read_year(self, year):
        d = self._all[self._all["date"].dt.year == year]
        return d[["date", "value"]]

    def download(self, year=None, force=False):
        """Rewrites the whole file (every year, ~3,000 rows); `year` is ignored."""
        names = ",".join(f"'{f}'" for f in self.facilities)
        r = requests.get(HATCHERY_URL, timeout=120, params={
            "$select": "date,facility,trapsite,stock,run,origin,adult_count,jack_count",
            "$where": f"species='Chinook' AND event='Trap Estimate' AND facility in ({names})",
            "$order": "date,facility", "$limit": 50000})
        r.raise_for_status()
        path = self.folder / self.filename
        old_rows = max(0, len(path.read_text().splitlines()) - 1) if path.exists() else 0
        new_rows = max(0, len(r.text.splitlines()) - 1)
        return self._save(path, lambda: path.write_text(r.text), new_rows, old_rows, force)


# ---------------------------------------------------------------------------
# The sources used by the dashboard. Order = order in menus and cards.
# ---------------------------------------------------------------------------
ALBION = (("Albion test fishery", 49.18, -122.56),)
BONNEVILLE = (("Bonneville Dam", 45.644, -121.94),)

_FOS_NOTE = ("CPUE is catch per thousand fathom minutes. Data is retrieved from the Fisheries and "
             "Oceans Canada [test fishery report website]"
             "(https://www-ops2.pac.dfo-mpo.gc.ca/fos2_Internet/Testfish/rptcsbdparm.cfm?stat=CPTFM&fsub_id={fsub}).")

albion_chinook = FOSTestFishery(
    "albion-chinook", "Albion Chinook (Fraser)", "foschinook", fsub_id=242, species="CHINOOK",
    units="CPUE", region="Fraser", sites=ALBION, lead_days=10,
    description=("Albion Chinook test fishery on the lower Fraser River at Albion, BC (near Fort "
                 "Langley). It fishes from early April to mid-October. " + _FOS_NOTE.format(fsub=242)
                 + " Read more about the [Albion Chinook gillnet]"
                 "(https://www.pac.dfo-mpo.gc.ca/fm-gp/fraser/docs/commercial/albionchinook-quinnat-eng.html)."))

bonneville = DartAdultCounts(
    "bonneville", "Bonneville Dam Chinook (Columbia)", "bonchinook",
    units="Count", region="Columbia", sites=BONNEVILLE, hist_digits=1, in_timing=False,
    description=("Bonneville Dam adult Chinook counts from Columbia Basin Research "
                 "[DART adult passage](https://www.cbr.washington.edu/dart/query/adult_daily). Fish are "
                 "counted directly April to October and by video in the other months; see the "
                 "[Fish Passage Center](https://www.fpc.org/adults/Q_adults_subsite.php)."))

# Bonneville's three Chinook runs, split by DART's date convention (timing chart only)
bonneville_runs = [
    DartAdultCounts(f"bonneville-{run.lower()}", f"Bonneville {run.lower()} Chinook", "bonchinook",
                    units="Count", region="Columbia", sites=BONNEVILLE, description="",
                    window=window, in_menu=False)
    for run, window in [("Spring", ("03-15", "05-31")), ("Summer", ("06-01", "07-31")),
                        ("Fall", ("08-01", "11-15"))]]

lake_washington = WDFWLakeWashington(
    "lake-washington", "Lake Washington Chinook (Ballard Locks)", "lakewash",
    units="Count", region="Puget Sound", sites=(("Ballard Locks", 47.665, -122.397),),
    description=("Lake Washington daily counts of adult Chinook passing the Hiram M. Chittenden "
                 "(Ballard) Locks in Seattle, from the Washington Department of Fish and Wildlife "
                 "[Lake Washington salmon counts](https://wdfw.wa.gov/fishing/reports/counts/lake-washington). "
                 "WDFW and the Muckleshoot Indian Tribe count the fish from late June to early October. "
                 "Past seasons were recovered from Wayback Machine copies (see data/lakewash/README.md)."))

ps_hatcheries = WDFWHatcheryReturns(
    "ps-hatcheries", "Puget Sound hatchery Chinook", "pshatchery",
    facilities=["SOOS CREEK HATCHERY", "ISSAQUAH HATCHERY", "VOIGHTS CR HATCHERY", "WALLACE R HATCHERY"],
    units="Weekly count", region="Puget Sound", weekly=True, hist_digits=2,
    sites=(("Soos Creek Hatchery", 47.31, -122.17), ("Issaquah Hatchery", 47.53, -122.04),
           ("Voights Creek Hatchery", 47.08, -122.18), ("Wallace River Hatchery", 47.87, -121.71)),
    description=("Puget Sound hatchery data is the weekly total of adult and jack Chinook arriving at the "
                 "traps of Soos Creek (Green River), Issaquah (Lake Washington), Voights Creek (Puyallup "
                 "River) and Wallace River (Skykomish River) hatcheries: the \"Trap Estimate\" records of "
                 "WDFW's [Hatchery Adult Salmon Returns]"
                 "(https://data.wa.gov/Natural-Resources-Environment/WDFW-Hatchery-Adult-Salmon-Returns/9q4e-xhag). "
                 "Counts are rounded estimates on irregular dates, and fish reach the hatcheries weeks after "
                 "passing through Puget Sound."))

albion_chum = FOSTestFishery(
    "albion-chum", "Albion chum (Fraser, fall prey)", "foschum", fsub_id=227, species="CHUM",
    units="CPUE", region="Fraser", sites=ALBION, fill_gaps=True,
    description=("Albion chum and coho data is from the DFO Albion chum gillnet test fishery on the "
                 "lower Fraser, which fishes every other day from September 1 to October 20 and daily to "
                 "the end of November. " + _FOS_NOTE.format(fsub=227) + " Chum and coho become a larger "
                 "share of the Southern Resident diet in the fall as Chinook decline."))

albion_coho = FOSTestFishery(
    "albion-coho", "Albion coho (Fraser, fall prey)", "foscoho", fsub_id=227, species="COHO",
    units="CPUE", region="Fraser", sites=ALBION, fill_gaps=True, in_timing=False, description="")

SALMON_SOURCES = [albion_chinook, bonneville, lake_washington, ps_hatcheries, albion_chum, albion_coho]

# Sources offered in the run-timing chart, in order
TIMING_SOURCES = [albion_chinook, *bonneville_runs, lake_washington, ps_hatcheries, albion_chum]

SOURCES_BY_KEY = {s.key: s for s in SALMON_SOURCES + TIMING_SOURCES}
