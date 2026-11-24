"""Acartia orca sightings: download the feed and tag Southern Resident reports.

Moved unchanged from scrapefunc.py (scrape_acartia, cleandates, proc_acartia
and the keyword lists). Only the default paths changed: they now point at
data/acartia/ inside the project, wherever the script is run from.

Writes:
  data/acartia/acartia_<YYYY-MM-DD>.csv  raw feed snapshot (git-ignored)
  data/acartia/srkw_<YYYY>.csv           confirmed + candidate SRKW rows
"""
import os
import re
from datetime import date
from datetime import datetime

import pandas as pd
import requests

from .config import DATA_DIR, PROJECT_ROOT

pd.options.mode.chained_assignment = None  # suppress chained assignment

ACARTIA_PATH = str(DATA_DIR / "acartia") + "/"


def scrape_acartia(acartia_path=ACARTIA_PATH):
    today = date.today()
    todaystr = str(today)

    # Read Acartia token
    try:
        atoken = open(PROJECT_ROOT / "acartia_token.txt").read()  # For debugging locally
    except:
        atoken = os.environ["ACARTIA_TOKEN"]  # For deployment

    # Acartia webpages
    url = "https://acartia.io/api/v1/sightings/"
    response = requests.get(
        url,
        headers={
            "Authorization": "Bearer " + atoken,
            "Content-Type": "application/json",
        },
    )
    acartia = pd.DataFrame(
        response.json(),
        columns=[
            "type", "created", "profile", "trusted", "entry_id",
            "latitude", "longitude", "photo_url", "signature", "ssemmi_id",
            "no_sighted", "submitter_did", "data_source_id", "data_source_name",
            "ssemmi_date_added", "data_source_entity", "data_source_witness",
            "data_source_comments",
        ],
    )
    acartia = acartia[
        ["type", "created", "latitude", "longitude",
         "no_sighted", "data_source_id", "data_source_comments"]
    ]
    acartia = acartia.drop_duplicates()
    acartia = acartia.sort_values(by=["created"])
    acartia.to_csv(acartia_path + "acartia_" + todaystr + ".csv", index=False)


def cleandates(s):
    if isinstance(s, str) and s.count('T') > 0:
        s = s.replace('T', ' ')
        s = s.replace('Z', '')
        s = s.split('.')[0]
    return s


# -------------------------------------------------------------------------
# proc_acartia — Southern Resident Killer Whale (SRKW) detection
# -------------------------------------------------------------------------
# Background: prior to ~Mar 7 2026 the Acartia feed used the `type` field to
# distinguish ecotypes ("Southern Resident Orca" vs plain "Orca" for Biggs).
# After that date most orca sightings come in as generic "Orca" with the
# ecotype information (when present at all) moved into data_source_comments,
# alongside three new explicit labels:
#     Killer whale(Bigg's (Transient))
#     Killer whale(Southern Resident)
#     Killer whale (Ecotype Unknown)
# This caused the strict SRKW detection rate to fall ~96% YoY (Mar-Apr 2025
# vs Mar-Apr 2026) without a corresponding drop in overall orca activity.
#
# Detection layers:
#   1. srkw_type      — `type` contains "Southern Resident"
#   2. srkw_generic   — comments contain "SRKW" / "Southern Resident"
#   3. J / K / L      — pod keywords or pod-specific individual IDs in comments
#                       (e.g. "J pod", "J35", "L82"; T-IDs explicitly excluded)
#   4. biggs          — `type` contains "Bigg"/"Transient", OR comments contain
#                       Biggs keywords, OR comments contain a T-ID (T19, T99s,
#                       T167A, T420, etc. — the Biggs/Transient catalog IDs)
#   5. srkw_candidate — orca-typed records with NO Biggs signal and NO
#                       confirmed-SRKW signal; flagged separately so downstream
#                       code can decide whether to include them
#
# Output columns (data/acartia/srkw_YYYY.csv):
#   - Existing columns retain their meaning: J, K, L, srkw, srkw_generic,
#     srkw_type, sum_jkl, biggs, sum_srkw_biggs, date, date_ymd, time, month,
#     day, year, m, plus all direction flags.
#   - New columns: biggs_type, biggs_comments, biggs_t_id, is_orca,
#     srkw_candidate, srkw_class ('confirmed' / 'candidate' / 'biggs' / 'other')
#   - Rows written: confirmed SRKW OR candidate SRKW. The dashboard's existing
#     `srkw==1` filter still returns strict counts unchanged. To opt in to
#     candidate coverage, change the filter downstream to
#     `(srkw == 1) | (srkw_candidate == 1)`.
# -------------------------------------------------------------------------

# SRKW keyword list — matched against lower-cased comments.
SRKW_KEYS = ['srkw', 'southern resident']

# J/K/L pod keyword lists — substring matched (case-sensitive; both cases listed
# explicitly to keep behavior identical to prior versions).
JPOD_KEYS = ['J pod', 'Jpod', 'J ppd', 'J-pod', 'Js',
             'j pod', 'jpod', 'j ppd', 'j-pod',
             'j+k', 'k+j', 'j & k', 'k & j', 'j and k', 'k and j', 'jk pods', 'kj pods',
             'J+K', 'K+J', 'J & K', 'K & J', 'J and K', 'K and J', 'JK pods', 'KJ pods',
             'j+l', 'l+j', 'j & l', 'l & j', 'j and l', 'l and j', 'jl pods', 'lj pods',
             'J+L', 'L+J', 'J & L', 'L & J', 'J and L', 'L and J', 'JL pods', 'LJ pods',
             'j, k, l pod', 'j, k, and l pod', 'jkl',
             'J, K, L pod', 'J, K, and L pod', 'JKL']

KPOD_KEYS = ['K pod', 'Kpod', 'K-pod', 'Ks',
             'k pod', 'kpod', 'k-pod',
             'j+k', 'k+j', 'j & k', 'k & j', 'j and k', 'k and j', 'jk pods', 'kj pods',
             'J+K', 'K+J', 'J & K', 'K & J', 'J and K', 'K and J', 'JK pods', 'KJ pods',
             'k+l', 'l+k', 'k & l', 'l & k', 'k and l', 'l and k', 'lk pods', 'kl pods',
             'K+L', 'L+K', 'K & L', 'L & K', 'K and L', 'L and K', 'LK pods', 'KL pods',
             'j, k, l pod', 'j, k, and l pod', 'jkl',
             'J, K, L pod', 'J, K, and L pod', 'JKL']

LPOD_KEYS = ['L pod', 'Lpod', 'L-pod', 'Ls',
             'j+l', 'l+j', 'j & l', 'l & j', 'j and l', 'l and j', 'jl pods', 'lj pods',
             'J+L', 'L+J', 'J & L', 'L & J', 'J and L', 'L and J', 'JL pods', 'LJ pods',
             'k+l', 'l+k', 'k & l', 'l & k', 'k and l', 'l and k', 'lk pods', 'kl pods',
             'K+L', 'L+K', 'K & L', 'L & K', 'K and L', 'L and K', 'LK pods', 'KL pods',
             'j, k, l pod', 'j, k, and l pod', 'jkl',
             'J, K, L pod', 'J, K, and L pod', 'JKL']

# Biggs/Transient keyword list — matched against lower-cased comments and type.
# Previously the list also included uppercase T-ID strings like 'T99', 'T137',
# which never matched because the haystack was lower-cased first. T-IDs are now
# handled by a regex pattern instead (which is the correct fix).
BIGGS_KEYS = ['bigg', 'transient']

# Orca/Killer Whale type indicators — used to identify which records are orcas
# at all, for the candidate-SRKW logic.
ORCA_TYPE_KEYS = ['orca', 'killer whale']

# Compiled regex patterns for individual-whale IDs in comments. Examples:
#   Biggs: T19, T46, T99s, T123, T137s, T167A, T420, T100E
#   J pod: J27, J35, J39, J50
#   K pod: K20, K37, K43
#   L pod: L72, L82, L113, L122
# Word boundaries prevent matches inside other words ('Tim', 'Kim', 'Largo').
# Suffixes of up to two letters cover plural pod groups ('T99s') and
# letter-suffixed individuals ('T167A', 'T100E').
_T_ID_RE = re.compile(r'\bT\d+[A-Za-z]{0,2}\b', re.IGNORECASE)
_J_ID_RE = re.compile(r'\bJ\d{1,3}\b', re.IGNORECASE)
_K_ID_RE = re.compile(r'\bK\d{1,3}\b', re.IGNORECASE)
_L_ID_RE = re.compile(r'\bL\d{1,3}\b', re.IGNORECASE)


def _contains_any(haystack, needles):
    """1 if any needle is a substring of haystack, else 0."""
    if not isinstance(haystack, str):
        return 0
    return 1 if any(n in haystack for n in needles) else 0


def _regex_hit(haystack, pattern):
    """1 if the compiled pattern finds a match in haystack, else 0."""
    if not isinstance(haystack, str):
        return 0
    return 1 if pattern.search(haystack) else 0


def proc_acartia(acartia_path=ACARTIA_PATH):
    today = date.today()
    todaystr = str(today)
    curyr = today.year

    acartia = pd.read_csv(acartia_path + 'acartia_' + todaystr + '.csv')
    acartia['created'] = pd.to_datetime(acartia['created'],errors='coerce')
    acartia = acartia.dropna(subset=['created'])

    # 2026 history snapshot was split off after the Mar 7 source change; stitch
    # the Feb snapshot back in so we have a continuous history.
    if curyr == 2026:
        acartia_feb = pd.read_csv(acartia_path + 'acartia_2026_feb.csv')
        acartia = pd.concat([acartia_feb, acartia], ignore_index=True)

    # print(acartia.tail(3))
    acartia = acartia[~acartia['created'].isnull()].copy()
    acartia['created'] = acartia['created'].apply(cleandates)
    acartia['m'] = pd.DatetimeIndex(acartia['created']).month
    acartia['day'] = pd.DatetimeIndex(acartia['created']).day
    acartia['year'] = pd.DatetimeIndex(acartia['created']).year
    acartia['month'] = acartia['m'].apply(lambda x: datetime.strptime(str(x), '%m').strftime('%b'))
    acartia['date'] = acartia[['month', 'day']].apply(lambda x: '-'.join(x.values.astype(str)), axis='columns')
    acartia['date_ymd'] = acartia[['year', 'm', 'day']].apply(lambda x: '-'.join(x.values.astype(str)), axis='columns')
    acartia['time'] = pd.DatetimeIndex(acartia['created']).time

    # Pre-stringify and lower-case for repeated lookups
    type_str = acartia['type'].fillna('').astype(str)
    type_lower = type_str.str.lower()
    comm_str = acartia['data_source_comments'].fillna('').astype(str)
    comm_lower = comm_str.str.lower()

    # ------------------------------------------------------------------
    # 1. Pod-specific signals from comments
    # ------------------------------------------------------------------
    # Substring keyword hits (existing logic; case-sensitive by design)
    j_kw = comm_str.apply(lambda x: _contains_any(x, JPOD_KEYS))
    k_kw = comm_str.apply(lambda x: _contains_any(x, KPOD_KEYS))
    l_kw = comm_str.apply(lambda x: _contains_any(x, LPOD_KEYS))
    # Individual-ID regex hits (new, generalized — formerly only J27/J35/J38/J40
    # etc. were enumerated; this catches all current SRKW catalog IDs)
    j_id = comm_str.apply(lambda x: _regex_hit(x, _J_ID_RE))
    k_id = comm_str.apply(lambda x: _regex_hit(x, _K_ID_RE))
    l_id = comm_str.apply(lambda x: _regex_hit(x, _L_ID_RE))

    acartia['J'] = ((j_kw == 1) | (j_id == 1)).astype(int)
    acartia['K'] = ((k_kw == 1) | (k_id == 1)).astype(int)
    acartia['L'] = ((l_kw == 1) | (l_id == 1)).astype(int)
    acartia['sum_jkl'] = acartia['J'] + acartia['K'] + acartia['L']

    # ------------------------------------------------------------------
    # 2. SRKW signals (strict / confirmed)
    # ------------------------------------------------------------------
    # Case-insensitive on `type` to cover both old ("Southern Resident Orca",
    # "Southern Resident Killer Whale") and new ("Killer whale(Southern
    # Resident)") label patterns.
    acartia['srkw_type'] = type_lower.apply(lambda x: 1 if 'southern resident' in x else 0)
    acartia['srkw_generic'] = comm_lower.apply(lambda x: 1 if any(k in x for k in SRKW_KEYS) else 0)
    acartia['srkw'] = acartia[['J', 'K', 'L', 'srkw_generic', 'srkw_type']].values.max(axis=1)

    # ------------------------------------------------------------------
    # 3. Biggs / Transient signals
    # ------------------------------------------------------------------
    # The new "Killer whale(Bigg's (Transient))" type label is caught by the
    # type-level check below. T-ID regex is the dominant signal in current data.
    acartia['biggs_type'] = type_lower.apply(lambda x: 1 if any(k in x for k in BIGGS_KEYS) else 0)
    acartia['biggs_comments'] = comm_lower.apply(lambda x: 1 if any(k in x for k in BIGGS_KEYS) else 0)
    acartia['biggs_t_id'] = comm_str.apply(lambda x: _regex_hit(x, _T_ID_RE))
    acartia['biggs'] = acartia[['biggs_type', 'biggs_comments', 'biggs_t_id']].values.max(axis=1)

    acartia['sum_srkw_biggs'] = acartia['srkw'] + acartia['biggs']

    # ------------------------------------------------------------------
    # 4. Candidate SRKW (recovery for the post-Mar-7 label regime)
    # ------------------------------------------------------------------
    # An "orca-typed" record with no Biggs evidence and no confirmed-SRKW
    # evidence. These are the sightings that previously came in tagged
    # "Southern Resident Orca" and now come in tagged generically "Orca".
    # We flag them but DO NOT set srkw=1, so the dashboard's `srkw==1` filter
    # keeps showing only high-confidence detections until you opt into using
    # candidates explicitly.
    acartia['is_orca'] = type_lower.apply(lambda x: 1 if any(k in x for k in ORCA_TYPE_KEYS) else 0)
    acartia['srkw_candidate'] = (
        (acartia['is_orca'] == 1)
        & (acartia['biggs'] == 0)
        & (acartia['srkw'] == 0)
    ).astype(int)

    # Single-string confidence label for convenience downstream
    acartia['srkw_class'] = 'other'
    acartia.loc[acartia['biggs'] == 1, 'srkw_class'] = 'biggs'
    acartia.loc[acartia['srkw_candidate'] == 1, 'srkw_class'] = 'candidate'
    acartia.loc[acartia['srkw'] == 1, 'srkw_class'] = 'confirmed'

    # ------------------------------------------------------------------
    # 5. Direction flags (unchanged from prior version)
    # ------------------------------------------------------------------
    acartia['south'] = comm_str.apply(
        lambda x: 1 if 'southbound' in str(x).lower() or 'heading south' in str(x).lower() else 0)
    acartia['southeast'] = comm_str.apply(
        lambda x: 1 if 'southeast' in str(x).lower() or 'SE' in str(x) else 0)
    acartia['southwest'] = comm_str.apply(
        lambda x: 1 if 'southwest' in str(x).lower() or 'SW' in str(x) else 0)
    acartia['north'] = comm_str.apply(
        lambda x: 1 if 'northbound' in str(x).lower() or 'heading north' in str(x).lower() else 0)
    acartia['northeast'] = comm_str.apply(
        lambda x: 1 if 'northeast' in str(x).lower() or 'NE' in str(x) else 0)
    acartia['northwest'] = comm_str.apply(
        lambda x: 1 if 'northwest' in str(x).lower() or 'NW' in str(x) else 0)
    acartia['east'] = comm_str.apply(
        lambda x: 1 if (('eastbound' in str(x).lower()) and ('southeastbound' not in str(x).lower()))
                       or ('heading east' in str(x).lower()) else 0)
    acartia['west'] = comm_str.apply(
        lambda x: 1 if (('westbound' in str(x).lower()) and ('northwestbound' not in str(x).lower()))
                       or ('heading west' in str(x).lower()) else 0)
    acartia['dir_sum'] = (acartia['south'] + acartia['southeast'] + acartia['southwest']
                          + acartia['north'] + acartia['northeast'] + acartia['northwest']
                          + acartia['east'] + acartia['west'])

    # ------------------------------------------------------------------
    # 6. Write current-year output. Include both confirmed AND candidate rows
    #    so downstream code can choose. `srkw==1` retains its strict meaning.
    # ------------------------------------------------------------------
    # Use range(2018, curyr+1) to reprocess all years; range(curyr, curyr+1) is
    # the incremental version for the daily scrape.
    for y in range(curyr, curyr + 1):
        act = acartia[acartia['year'] == y]
        act = act[(act['srkw'] == 1) | (act['srkw_candidate'] == 1)]
        act = act.drop_duplicates()
        act.to_csv(acartia_path + 'srkw_' + str(y) + '.csv', index=False)

    # Quick summary for the scraper log
    cur = acartia[acartia['year'] == curyr]
    print(f"[proc_acartia] {curyr}: "
          f"{int((cur['srkw'] == 1).sum())} confirmed SRKW, "
          f"{int((cur['srkw_candidate'] == 1).sum())} candidate SRKW, "
          f"{int((cur['biggs'] == 1).sum())} Biggs, "
          f"{len(cur)} total records.")
