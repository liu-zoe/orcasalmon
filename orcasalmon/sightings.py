"""Southern Resident orca sightings.

Two SightingSource subclasses read the two data sets into the same standard
columns, so the rest of the code (filters, sighting days, timing) is written once:

  date            day of the sighting (Timestamp, no time)
  label           text shown when hovering on the map
  latitude, longitude
  J, K, L         1 if that pod was reported, else 0
  status          "Confirmed", or "Candidate" for Acartia reports typed only as
                  "Orca" since Acartia's March 2026 label change (see acartia.py)
  central_salish  True if in the central Salish Sea (north of Admiralty Inlet)
  source          "The Whale Museum" or "Acartia"

We count sighting DAYS rather than reports, so one busy whale-watching day
with 40 reports counts once; that reduces (but doesn't remove) the effect of
how many people are out looking.
"""
import math
import os
import re
from functools import lru_cache

import pandas as pd

from .config import CENTRAL_SALISH_LAT, CURYR, DATA_DIR

PODS = ["All pods", "J pod", "K pod", "L pod"]


class SightingSource:
    """Base class: one sightings data set, one file per year."""
    name = ""
    folder = None
    pattern = None          # regex for file names, with one (\d{4}) group
    first_year = None       # ignore files before this year

    def years(self):
        if not self.folder.is_dir():  # e.g. a public copy without the sightings data
            return []
        ys = [int(m.group(1)) for f in os.listdir(self.folder)
              if (m := re.fullmatch(self.pattern, f))]
        return sorted(y for y in ys if self.first_year is None or y >= self.first_year)

    def read_year(self, year):
        raise NotImplementedError

    @staticmethod
    def _fix_longitude(lon):
        # some files store coordinates as text, and a few reports have the
        # sign dropped (123.2 instead of -123.2)
        lon = pd.to_numeric(lon, errors="coerce")
        return lon.where(~lon.between(115, 135), -lon)


class TheWhaleMuseum(SightingSource):
    """The Whale Museum's Southern Resident sighting archive (1990-2021).
    Rows without a pod ("orcas", "srs") still count as Southern Residents."""
    name = "The Whale Museum"
    folder = DATA_DIR / "twm"
    pattern = r"twm(\d{4})\.csv"
    first_year = 1990

    def read_year(self, year):
        d = pd.read_csv(self.folder / f"twm{year}.csv")
        dates = pd.to_datetime(d["SightDate"], errors="coerce")
        return pd.DataFrame({
            "date": dates,
            "label": "[TWM] " + d["SightDate"].astype(str) + " " + d["Time1"].astype(str),
            "latitude": pd.to_numeric(d["latitude"], errors="coerce"),
            "longitude": self._fix_longitude(d["longitude"]),
            "J": d["j"].fillna(0).astype(int), "K": d["k"].fillna(0).astype(int),
            "L": d["l"].fillna(0).astype(int),
            "status": "Confirmed",
            "central_salish": d["central_salish"] == 1,
            "source": self.name,
        })


class Acartia(SightingSource):
    """Acartia's crowd-sourced sightings (2018 onward), as tagged by
    acartia.proc_acartia(): srkw == 1 is a confirmed Southern Resident report,
    srkw_candidate == 1 an untyped orca report with no Bigg's signal."""
    name = "Acartia"
    folder = DATA_DIR / "acartia"
    pattern = r"srkw_(\d{4})\.csv"

    def read_year(self, year):
        d = pd.read_csv(self.folder / f"srkw_{year}.csv")
        d["status"] = "Other"
        if "srkw_candidate" in d:  # older files predate the candidate flag
            d.loc[d["srkw_candidate"] == 1, "status"] = "Candidate"
        d.loc[d["srkw"] == 1, "status"] = "Confirmed"
        d = d[d["status"] != "Other"]
        return pd.DataFrame({
            "date": pd.to_datetime(d["date_ymd"], format="%Y-%m-%d", errors="coerce"),
            "label": "[Acartia] " + d["created"].astype(str),
            "latitude": pd.to_numeric(d["latitude"], errors="coerce"),
            "longitude": self._fix_longitude(d["longitude"]),
            "J": d["J"], "K": d["K"], "L": d["L"],
            "status": d["status"],
            "central_salish": d["latitude"] > CENTRAL_SALISH_LAT,
            "source": self.name,
        })


SIGHTING_SOURCES = [TheWhaleMuseum(), Acartia()]


def sighting_years():
    """Every year that at least one source covers, newest first."""
    return sorted({y for s in SIGHTING_SOURCES for y in s.years()}, reverse=True)


@lru_cache(maxsize=64)
def _load_year(year):
    frames = [s.read_year(year) for s in SIGHTING_SOURCES if year in s.years()]
    if not frames:  # no sightings data for this year (or none at all)
        return pd.DataFrame({"date": pd.Series(dtype="datetime64[ns]"), "label": pd.Series(dtype=str),
                             "latitude": pd.Series(dtype=float), "longitude": pd.Series(dtype=float),
                             "J": pd.Series(dtype=int), "K": pd.Series(dtype=int), "L": pd.Series(dtype=int),
                             "status": pd.Series(dtype=str), "central_salish": pd.Series(dtype=bool),
                             "source": pd.Series(dtype=str), "month": pd.Series(dtype=int)})
    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=["date", "latitude", "longitude"])
    df = df[df["date"].dt.year == year]
    df["month"] = df["date"].dt.month
    return df.reset_index(drop=True)


def load_sightings(year, pod="All pods"):
    """All confirmed and candidate sightings for a year. Choosing a pod keeps
    only reports naming that pod (candidates never name one, so they drop out)."""
    df = _load_year(int(year))
    if pod and pod != "All pods":
        df = df[df[pod[0]] == 1]
    return df


def weekly_sighting_days(year, pod="All pods"):
    """Days per week (0-7) with a central Salish Sea sighting: confirmed days,
    and extra days that only have candidate reports. Week 0 = Jan 1-7."""
    df = load_sightings(year, pod)
    df = df[df["central_salish"]]
    conf = set(df.loc[df["status"] == "Confirmed", "date"])
    cand = set(df.loc[df["status"] == "Candidate", "date"]) - conf
    out = pd.DataFrame({"week": range(53)})
    for col, days in [("confirmed", conf), ("candidate", cand)]:
        weeks = pd.Series([(d.dayofyear - 1) // 7 for d in days], dtype=int)
        out[col] = out["week"].map(weeks.value_counts()).fillna(0).astype(int)
    return out


def sighting_days_to_date(year, through, pod="All pods"):
    """(confirmed days, candidate-only days) in the central Salish Sea from
    Jan 1 through the month/day of `through`."""
    df = load_sightings(year, pod)
    md = df["date"].dt.month * 100 + df["date"].dt.day
    df = df[df["central_salish"] & (md <= through.month * 100 + through.day)]
    conf = set(df.loc[df["status"] == "Confirmed", "date"])
    cand = set(df.loc[df["status"] == "Candidate", "date"]) - conf
    return len(conf), len(cand)


@lru_cache(maxsize=16)
def sighting_timing(pod="All pods", include_candidates=False):
    """Run-timing style table for sightings: for each year, the day of year by
    which 25%, 50% and 75% of that year's central Salish Sea sighting days
    had happened. Columns: year, q25, q50, q75."""
    rows = []
    for y in sorted(sighting_years()):
        df = load_sightings(y, pod)
        df = df[df["central_salish"]]
        if not include_candidates:
            df = df[df["status"] == "Confirmed"]
        doys = sorted({d.dayofyear for d in df["date"]})
        if not doys:
            continue
        # first day by which at least share q of the year's sighting days had passed
        rows.append([y] + [doys[max(0, math.ceil(q * len(doys)) - 1)] for q in (0.25, 0.5, 0.75)])
    return pd.DataFrame(rows, columns=["year", "q25", "q50", "q75"])
