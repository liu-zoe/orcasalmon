# %% [markdown]
# Script Name: scrapper.py
# <br>Purpose: Scrapping chinook data and orca for dashboard
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
curyr=today.year
#curyr=2022
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
chromedriver_autoinstaller.install()  # Check if the current version of chromedriver exists
                                      # and if it doesn't exist, download it automatically,
                                      # then add chromedriver to path

# %%
def scrap_fos(yrs='2022',spe='CHINOOK SALMON', fos_path=fos_path):
  #Set up chrome driver
  options = webdriver.ChromeOptions()
  options.add_argument('--headless')
  options.add_argument('--no-sandbox')
  options.add_argument('--disable-dev-shm-usage')
  options.add_argument('--ignore-certificate-errors')
  driver=webdriver.Chrome(options=options)
  #landing page of fos data
  url = 'https://www-ops2.pac.dfo-mpo.gc.ca/fos2_Internet/Testfish/rptcsbdparm.cfm?stat=CPTFM&fsub_id=242'
  driver.get(url)
  sleep(3)
  #select year and species and generate report
  driver.find_element('id','lboYears').send_keys(yrs)
  driver.find_element('id','lboSpecies').send_keys(spe)
  driver.find_element('name','cmdRunReport').click()
  sleep(1)
  window_after = driver.window_handles[1] #Switch to the newly opened window
  driver.switch_to.window(window_after)
  #scrape data from the report table 
  table=driver.find_elements(By.XPATH,'.//tr')
  #process scrapped data and convert to pandas df
  tabls0=list(map(lambda x: x.text.split(sep=' '), table))
  tabls=[t for t in tabls0 if ((len(t)==12) & (t[0]!='Printed'))]
  dat=pd.DataFrame(tabls, columns=['day','mon','year','netlen','catch1','sets1','effort1','cpue1', 'catch2','sets2','effort2','cpue2'])
  #archive data to csv
  if os.path.exists(fos_path)==False:
    os.makedirs(fos_path)
  dat.to_csv(fos_path+'fos'+yrs+'.csv', index=False)

# %% [markdown]
# Use the following line to download the current year

# %%
scrap_fos(yrs=str(curyr),spe='CHINOOK SALMON', fos_path=fos_path)

# %% [markdown]
# Use the following lines to download all fos chinook data
# <br>Note: commented out after running it once

# %%
'''
for y in ayl:
  scrap_fos(yrs=str(y),spe='CHINOOK SALMON', fos_path=fos_path)
'''

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
  driver.find_element('id','calendar').click()
  driver.find_element('id','run1').click()
  driver.find_element(By.XPATH, ".//input[@type='submit']").click()
  sleep(3)
  dlf=[x for x in os.listdir("/content") if x[-4:]=='.csv']
  filename=dlf[0]
  os.rename('/content/'+filename, bon_path+'bon'+yrs+'.csv')

# %% [markdown]
# Use the following line to download the current year

# %%
scrap_bon(yrs=str(curyr), bon_path=bon_path)

# %% [markdown]
# Use the following lines to download all fos chinook data
# <br>Note: commented out after running it once

# %%
'''
for y in byl:
  scrap_bon(yrs=str(y), bon_path=bon_path)
'''

# %% [markdown]
# 2.3 Scrap Acartia orca data

# %%
def scrap_acartia(acartia_path='./data/acartia/'):
  #Read Acartia token
  #f = open('/content/drive/MyDrive/Orcasound/salmon/acartia_token.txt', 'r')
  atoken='jH0zM5fqOxqJVVJc2j8u218svEDapzPa'
  #Acartia webpages
  url='https://acartia.io/api/v1/sightings/'
  response = requests.get(url, headers={'Authorization': 'Bearer '+atoken, 
                                     'Content-Type': 'application/json'})
  acartia=pd.DataFrame(response.json(), 
                     columns=['type','created','profile','trusted','entry_id','latitude','longitude','photo_url','signature',
                              'ssemmi_id','no_sighted','submitter_did','data_source_id',
                              'data_source_name','ssemmi_date_added','data_source_entity', 'data_source_witness', 'data_source_comments'])
  acartia=acartia[['type','created','latitude','longitude','no_sighted','data_source_id','data_source_comments']]
  acartia=acartia.drop_duplicates()
  acartia=acartia.sort_values(by=['created'])
  #save acartia to the Colab local folder ***disappear after each session!!!
  acartia.to_csv(acartia_path+'acartia_'+todaystr+'.csv', index=False)
# %% [markdown]
# Run the following code to scrape Acartia data

# %%
scrap_acartia()

# %% [markdown]
# Processing Acartia Data

# %%
acartia=pd.read_csv(acartia_path,'acartia_'+todaystr+'.csv')
srkw=acartia[acartia['type']=='Southern Resident Killer Whale']
srkw['m']=pd.DatetimeIndex(srkw['created']).month
srkw['day']=pd.DatetimeIndex(srkw['created']).day
srkw['year']=pd.DatetimeIndex(srkw['created']).year
srkw['month']=srkw['m'].apply(lambda x: datetime.strptime(str(x), '%m').strftime('%b'))
srkw['date']=srkw[['month','day']].apply(lambda x: '-'.join(x.values.astype(str)), axis="columns")
srkw['date_ymd']=srkw[['year','m','day']].apply(lambda x: '-'.join(x.values.astype(str)), axis="columns")

srkw['J']=srkw['data_source_comments'].apply(lambda x: 1 if ('J pod' in str(x))
or ('J Pod' in str(x)) or ('jpod' in str(x)) or ('j pod' in str(x)) or ('J ppd' in str(x))
or ('Jpod' in str(x)) 
or ('J-pod' in str(x)) or ('J-Pod' in str(x))
or ('J+K pod' in str(x)) or ('J & K pod' in str(x)) or ('J and K pod' in str(x))
or ('J+L pod' in str(x)) or ('L+J pod' in str(x))
or ('J, K, L pod' in str(x)) or ('JKL' in str(x)) or ('J, K, and L pod' in str(x))
or ('Js' in str(x)) or ('js' in str(x))
or ('J27' in str(x)) or ('J38' in str(x)) or ('J35'in str(x)) or ('J40' in str(x))
else 0)

srkw['K']=srkw['data_source_comments'].apply(lambda x: 1 if ('K pod' in str(x))
or ('Kpod' in str(x)) or ('K-pod' in str(x)) or ('Ks' in str(x)) or ('K Pod' in str(x))
or ('J+K pod' in str(x))
or ('K+L' in str(x)) or ('K and L' in str(x))
or ('J, K, L pod' in str(x)) or ('J & K pod' in str(x)) or ('JKL' in str(x)) or ('J, K, and L pod' in str(x))
or ('K37' in str(x))
else 0)

srkw['L']=srkw['data_source_comments'].apply(lambda x: 1 if ('L pod' in str(x))
or ('L Pod' in str(x)) or ('Lpod' in str(x)) or ('L-pod' in str(x)) or ('Ls' in str(x)) 
or ('L12' in str(x)) or ('L54' in str(x)) or ('L-12' in str(x)) or ('L85' in str(x))
or ('L82' in str(x)) or ('L87' in str(x))
or ('J+L pod' in str(x)) or ('L+J pod' in str(x))
or ('K+L' in str(x)) or ('K and L' in str(x))
or ('J, K, L pod' in str(x)) or ('JKL' in str(x)) or ('J, K, and L pod' in str(x))
else 0)

srkw['biggs']=srkw['data_source_comments'].apply(lambda x: 1 if ('biggs' in str(x).lower()) else 0)

srkw['sum_jkl']=srkw['J']+srkw['K']+srkw['L']
srkw['sum_jkl_biggs']=srkw['J']+srkw['K']+srkw['L']+srkw['biggs']
srkw['south']=srkw['data_source_comments'].apply(lambda x: 1 if ('southbound') in str(x).lower()
or ('heading south' in str(x).lower())
else 0)

srkw['southeast']=srkw['data_source_comments'].apply(lambda x: 1 if ('southeast') in str(x).lower()
or ('SE' in str(x))
else 0)

srkw['southwest']=srkw['data_source_comments'].apply(lambda x: 1 if ('southwest') in str(x).lower()
or ('SW' in str(x))
else 0)

srkw['north']=srkw['data_source_comments'].apply(lambda x: 1 if ('northbound') in str(x).lower()
or ('heading north' in str(x).lower())
else 0)

srkw['northeast']=srkw['data_source_comments'].apply(lambda x: 1 if ('northeast') in str(x).lower()
or ('NE' in str(x))
else 0)

srkw['northwest']=srkw['data_source_comments'].apply(lambda x: 1 if ('northwest') in str(x).lower()
or ('NW' in str(x))
else 0)

srkw['east']=srkw['data_source_comments'].apply(lambda x: 1 if (('eastbound') in str(x).lower() and ('southeastbound') not in str(x).lower())
or ('heading east' in str(x).lower())
else 0)

srkw['west']=srkw['data_source_comments'].apply(lambda x: 1 if (('westbound') in str(x).lower() and ('northwestbound' not in str(x).lower()))
or ('heading west' in str(x).lower())
else 0)

srkw['dir_sum']=srkw['south']+srkw['southeast']+srkw['southwest']+srkw['north']+srkw['northeast']+srkw['northwest']+srkw['east']+srkw['west']

srkw_curyr=srkw[srkw['year']==curyr]
#srkw_lastyear=srkw[srkw['year']==(curyr-1)]
#srkw_2yr=srkw[srkw['year']==(curyr-2)]
#srkw_3yr=srkw[srkw['year']==(curyr-3)]

srkw_curyr.to_csv(acartia_path+'srkw_'+str(curyr)+'.csv', index=False)
#srkw_lastyear.to_csv(acartia_path+'srkw_'+str(curyr-1)+'.csv', index=False)
#srkw_2yr.to_csv(acartia_path+'srkw_'+str(curyr-2)+'.csv', index=False)
#srkw_3yr.to_csv(acartia_path+'srkw_'+str(curyr-3)+'.csv', index=False)
