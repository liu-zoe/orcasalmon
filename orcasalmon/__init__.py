"""orcasalmon: data sources, analysis and charts for the Chinook and orca dashboard.

Modules
-------
config     paths, dates and constants shared by everything else
salmon     SalmonSource classes: one per salmon data source (download + load)
sightings  SightingSource classes: orca sightings from The Whale Museum and Acartia
acartia    downloading Acartia sightings and tagging Southern Resident reports
timing     run-timing and "% of normal" calculations
charts     Plotly figures used by the dashboard
layout     the page layout (Dash components)
callbacks  the Dash callbacks that connect menus to charts
"""
