"""Paths, dates and constants used across the package."""
from datetime import date
from pathlib import Path

# Folders
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Dates. TODAY is evaluated once when the app starts (the server is restarted
# on each deploy, and the data only changes weekly).
TODAY = date.today()
CURYR = TODAY.year

# How many earlier years make up "normal" for the status cards
NORMAL_YEARS = 10

# Southern Resident sightings north of this latitude count as the
# central Salish Sea (north of the Admiralty Inlet entrance to Puget Sound).
CENTRAL_SALISH_LAT = 48.19437

# A leap year used to place month/day values on a date axis, so Feb 29 fits
REFERENCE_YEAR = 2024

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
