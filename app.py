## Project Name: Orcasound Salmon
### Program Name: app.py
### Purpose: Dash dashboard of Chinook salmon runs and Southern Resident orca sightings
##### Date Created: Dec 14th 2024
##### Restructured: Nov 24th 2026 (code moved into the orcasalmon/ package)
#
# The data loading, charts, layout and callbacks live in orcasalmon/.
# Deployment runs `gunicorn app:server` (see Procfile), so `server` must stay here.
# Run locally with:  python app.py   then open http://127.0.0.1:8050

import dash

from orcasalmon.callbacks import register
from orcasalmon.layout import build_layout

app = dash.Dash(
    __name__,
    title="Chinook and Orca",
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
        {"name": "description", "content": "Chinook salmon runs and Southern Resident orca sightings"},
        {"name": "news_keywords", "content": "Chinook, Salmon, Orca, Killer Whales, Puget Sound"},
    ],
)
server = app.server
app.layout = build_layout(app)
register(app)

if __name__ == "__main__":
    app.run(debug=False)
