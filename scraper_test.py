# %% [markdown]
# Script Name: scraper.py
# <br>Purpose: Scraping chinook data and orca for dashboard
# <br>Author: Zoe Liu
# <br>Date: Oct 12th 2022

# %% [markdown]
# #### 1 Setup

# %% [markdown]
# 1.1 Import libraries

# %%
import os
import re

import requests
import selenium
from selenium import webdriver 
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By

import chromedriver_autoinstaller

from datetime import date
from datetime import datetime
from time import strptime
import time
from time import sleep

import pandas as pd
pd.options.mode.chained_assignment = None #suppress chained assignment 

# %% [markdown]
# 1.2 Get today's date

# %%
today=date.today()
todaystr=str(today)
#curyr=today.year
curyr=2024
lastyr=curyr-1
twoyr=curyr-2
ayl=[y for y in range(1980, curyr+1)] #year list for Albion
byl=[y for y in range(1939, curyr+1)] #year list for Bonneville Dam

# %% [markdown]
# 1.3 Define data path

# %%
fos_path='./data/foschinook/'
bon_path='./data/bonchinook/'
acartia_path='./data/acartia/'
# %% [markdown]
# #### 2 Scap web data

# %% [markdown]
# 2.1 Scrap Chinook data by year
#chromedriver_autoinstaller.install()  # Check if the current version of chromedriver exists
                                      # and if it doesn't exist, download it automatically,
                                      # then add chromedriver to path


# %% [markdown]
# 2.2 Scrap Bonneville Dam Chinook Daily count

# %%
def scrap_bon(yrs='2022', bon_path=bon_path):
  if os.path.exists(bon_path)==False:
    os.makedirs(bon_path)
  #Set up chrome driver
  options = webdriver.ChromeOptions()
  options.add_argument('--headless')
  options.add_argument('--no-sandbox')
  options.add_argument('--disable-dev-shm-usage')
  options.add_argument('--ignore-certificate-errors')
  driver=webdriver.Chrome(options=options)
  #landing page of Columbia Basin Research 
  url = 'https://www.cbr.washington.edu/dart/query/adult_daily'
  driver.get(url)
  sleep(3)
  #select year and generate report
  site='BON'
  driver.find_element('id','daily').click()
  driver.find_element('id','outputFormat2').click()
  driver.find_element('id','year-select').send_keys(yrs)
  driver.find_element('id','proj-select').send_keys(site)
  if driver.find_element('id','calendar').is_selected()==False:
    print("click the calendar element")
    driver.find_element('id','calendar').submit()
  if driver.find_element('id','run1').is_selected()==False:
    print("click the run1 element")
    driver.find_element('id','run1').submit()  
  driver.find_element(By.XPATH, ".//input[@type='submit']").submit()
  sleep(3)
  dlf=[x for x in os.listdir("./") if x[-4:]=='.csv']
  filename=dlf[0]
  os.rename('./'+filename, bon_path+'bon'+yrs+'.csv')

# %% [markdown]
# Use the following line to download the current year

# %%
scrap_bon(yrs=str(curyr), bon_path=bon_path)
