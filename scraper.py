### Script Name: scraper.py
# Purpose: Scraping chinook data and orca for dashboard
# Author: Zoe Liu
# Date: Oct 12th 2022
# Updated: Dec 8th 2024

#### 1 Setup
# 1.1 Import libraries
from datetime import date
import pandas as pd
pd.options.mode.chained_assignment = None #suppress chained assignment
from scrapefunc import (scrape_fos, scrape_bon,scrape_acartia, proc_acartia)

# 1.2 Get today's date
today=date.today()
todaystr=str(today)
curyr=today.year
lastyr=curyr-1
twoyr=curyr-2
ayl=[y for y in range(1980, curyr+1)] #year list for Albion
byl=[y for y in range(1939, curyr+1)] #year list for Bonneville Dam

# 1.3 Define data path
fos_path='./data/foschinook/'
bon_path='./data/bonchinook/'
acartia_path='./data/acartia/'

##### 2 Scap web data
# 2.1 Scrape Chinook data by year

# Use the following line to download the current year
scrape_fos(yrs=str(curyr),spe='CHINOOK SALMON')

# Use the following lines to download all fos chinook data
# Note: commented out after running it once
'''
for y in ayl:
  scrape_fos(yrs=str(y),spe='CHINOOK SALMON', fos_path=fos_path)
'''

# 2.2 Scrape Bonneville Dam Chinook Daily count
# Use the following line to download the current year
scrape_bon(yrs=str(curyr), bon_path=bon_path)

# Use the following lines to download all fos chinook data
#Note: commented out after running it once
'''
for y in byl:
  scrape_bon(yrs=str(y), bon_path=bon_path)
'''

# 2.3 Scrape Acartia orca data
# Run the following code to scrape Acartia data
scrape_acartia(acartia_path=acartia_path)

# Processing Acartia Data
proc_acartia(acartia_path)