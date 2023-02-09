#%% [markdown]
## Project Name: Orcasound Salmon
### Program Name: app.py
### Purpose: To make a dash board for the Chinook salmon data
##### Date Created: Dec 3rd 2022
import os
import pathlib
import glob

from datetime import date
from datetime import datetime as dt 
from time import strptime
from time import sleep

import pandas as pd
pd.options.mode.chained_assignment = None #suppress chained assignment 

import numpy as np

import dash
from dash import dcc
from dash import html 
from dash.dependencies import Input, Output, State

import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.express as px
#%%
# Initialize app
app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
        {"name": "description", "content": "Chinook Salmon Dashboard"}, 
        {"name": "news_keywords", "content": "Chinook, Salmon, Orca, Killer Whales, Puget Sound"}
        ],
    )
server=app.server
#%%
#--------------------------Load And Process Data----------------------------#
APP_PATH = str(pathlib.Path(__file__).parent.resolve())
mapbox_access_token = os.environ['MAPBOX_TOKEN']
#mapbox_access_token = open(os.path.join(APP_PATH,"mapbox_token.txt")).read()
#Get dates
today=date.today()
todaystr=str(today)
curyr=today.year
#curyr=2022
lastyr=curyr-1
twoyr=curyr-2
ayl=[y for y in range(1980, curyr+1)] #year list for Albion
byl=[y for y in range(1939, curyr+1)] #year list for Bonneville Dam

#Define data path
fos_path=os.path.join(APP_PATH,'data/foschinook/')
bon_path=os.path.join(APP_PATH,'data/bonchinook/')
acartia_path=os.path.join(APP_PATH, 'data/acartia/')
#%%
#Load Albion data
albion=pd.DataFrame(columns=['day','m'])
for i in reversed(range(len(ayl))):
    d=pd.read_csv(fos_path+'fos'+str(ayl[i])+'.csv',\
        usecols=['day','mon','cpue1'])
    d['m']=d['mon'].apply(lambda x: dt.strptime(x, '%b').month)
    d=d.drop(columns='mon')
    d=d.rename(columns={'cpue1':'cpue'+str(ayl[i])})
    albion=pd.merge(left=albion, right=d, how='outer', on=['m','day'], sort=True)
del(d,i)
albion['cpue_hist']=albion.iloc[:,5:].mean(axis=1, skipna=True).round(decimals=2) #History up to 3 years ago
albion['cpue_hist2']=albion.iloc[:,3:].mean(axis=1, skipna=True).round(decimals=2) #History up to last year
albion['month']=albion['m'].apply(lambda x: dt.strptime(str(x), '%m').strftime('%b'))
albion['date']=albion[['month','day']].apply(lambda x: '-'.join(x.values.astype(str)), axis="columns")
# %%
# Create Albion lag dataset -- Current Year
lag1=4
albion_curyr_lagged=albion[['date','cpue'+str(curyr),'cpue'+str(curyr-1),'cpue_hist']]
albion_curyr_lagged['date1']=pd.to_datetime(albion_curyr_lagged['date'], format='%b-%d')
albion_curyr_lagged['date2']=albion_curyr_lagged['date1'] + pd.Timedelta(days=lag1)
albion_curyr_lagged['m']=pd.DatetimeIndex(albion_curyr_lagged['date2']).month
albion_curyr_lagged['day']=pd.DatetimeIndex(albion_curyr_lagged['date2']).day
albion_curyr_lagged=albion_curyr_lagged.drop(columns=['date','date1','date2'])
# %%
# Load Bonneville Dam data
bonnev=pd.DataFrame(columns=['day','m'])
for i in reversed(range(len(byl))):
    d=pd.read_csv(bon_path+'bon'+str(byl[i])+'.csv',\
        usecols=['Project','Date','Chin'])
    d=d[d['Project']=='Bonneville']
    d['Chin2']=d['Chin'].apply(lambda x: 0 if x<0 else x)
    d['m']=pd.DatetimeIndex(d['Date']).month
    d['day']=pd.DatetimeIndex(d['Date']).day
    d=d.rename(columns={'Chin2':'chin'+str(byl[i])})
    d=d.drop(columns=['Project','Date','Chin'])
    bonnev=pd.merge(left=bonnev, right=d, how='outer', on=['m','day'], sort=True)
del(d,i)
bonnev['chin_hist']=bonnev.iloc[:,5:].mean(axis=1, skipna=True).round(decimals=1)#History up to 3 years ago
bonnev['chin_hist2']=bonnev.iloc[:,3:].mean(axis=1, skipna=True).round(decimals=1)#History up to last year
bonnev['month']=bonnev['m'].apply(lambda x: dt.strptime(str(x), '%m').strftime('%b'))
bonnev['date']=bonnev[['month','day']].apply(lambda x: '-'.join(x.values.astype(str)), axis="columns")
# %% 
# Create Bonneville Dam lagged data -- Current Year
lag2=10
bonnev_curyr_lagged=bonnev[['date','chin'+str(curyr),'chin'+str(curyr-1),'chin_hist']]
bonnev_curyr_lagged=bonnev_curyr_lagged[bonnev_curyr_lagged['date']!='Feb-29']
bonnev_curyr_lagged['date1']=pd.to_datetime(bonnev_curyr_lagged['date'].apply(lambda x: str(curyr-1)+'-'+x), format='%Y-%b-%d')
bonnev_curyr_lagged['date2']=bonnev_curyr_lagged['date1'] + pd.Timedelta(days=lag2)
bonnev_curyr_lagged['m']=pd.DatetimeIndex(bonnev_curyr_lagged['date2']).month
bonnev_curyr_lagged['day']=pd.DatetimeIndex(bonnev_curyr_lagged['date2']).day
bonnev_curyr_lagged=bonnev_curyr_lagged.drop(columns=['date','date1','date2'])
# %%
# Create calendar dataframes 
cal1=bonnev[['date']]
cal1=cal1[cal1['date']!='Feb-29']
cal1['date1']=pd.to_datetime(cal1['date'].apply(lambda x: str(curyr)+'-'+x), format='%Y-%b-%d')
cal1['m']=pd.DatetimeIndex(cal1['date1']).month
cal1['day']=pd.DatetimeIndex(cal1['date1']).day
cal1=cal1.drop(columns=['date1'])
# Example data frame
# date  m day
# Jan-1 1 1 
# %%
cal2=bonnev[['date']]
cal2['date1']=pd.to_datetime(cal2['date'].apply(lambda x: str(curyr)+'-'+x), errors='coerce', format='%Y-%b-%d')
cal2['m']=pd.DatetimeIndex(cal2['date1']).month
cal2['day']=pd.DatetimeIndex(cal2['date1']).day
cal2=cal2.drop(columns=['date1'])
# Example data frame
# date  m   day
# Jan-1 1.0 1.0 
#%%
albion=albion.drop(columns=['date'])
albion=cal1.merge(albion, how='left', on=['m','day'])
# %%
lagged=cal1.merge(bonnev_curyr_lagged, how='left', on=['m','day'])
lagged=lagged.merge(albion_curyr_lagged, on=['m','day'], how='left')
# %% [markdown]
# Loading Acartia data
srkw_files=glob.glob(acartia_path+"srkw_"+str(curyr)+".csv")
srkw_files.sort(reverse=True)
srkwc=pd.read_csv(srkw_files[0])
srkwc['date2']=pd.to_datetime(srkwc['date_ymd'],format='%Y-%m-%d', errors='coerce')
srkwc['day_of_year']=srkwc['date_ymd'].apply(lambda x: pd.Period(x, freq='D').day_of_year)
srkwc_k=srkwc[srkwc.K==1].reset_index()
srkwc_l=srkwc[srkwc.L==1].reset_index()
srkwc_j=srkwc[srkwc.J==1].reset_index()
#%%
srkw_curyr_count=srkwc[['m','day','date']]
srkw_curyr_count=srkw_curyr_count['date'].value_counts().reset_index()
srkw_curyr_count=srkw_curyr_count.rename(columns={'date':'count', 'index':'date'})
srkw_curyr_count['day']=srkw_curyr_count['date'].apply(lambda x: x.split('-')[1])
srkw_curyr_count['mon']=srkw_curyr_count['date'].apply(lambda x: x.split('-')[0])
srkw_curyr_count['m']=srkw_curyr_count['mon'].apply(lambda x: dt.strptime(x, '%b').month)
srkw_curyr_count['m2']=srkw_curyr_count['m'].astype('float')
srkw_curyr_count['day2']=srkw_curyr_count['day'].astype('float')
srkw_curyr_count=srkw_curyr_count.sort_values(by=['m2','day2'])
srkw_curyr_count=srkw_curyr_count.merge(lagged, left_on=['m2','day2'], right_on=['m','day'], how='right')
srkw_curyr_count=srkw_curyr_count[['date_y', 'm_y','day_y','count','chin'+str(curyr),'chin'+str(curyr-1),'chin_hist','cpue'+str(curyr),'cpue'+str(curyr-1),'cpue_hist']]
srkw_curyr_count.columns=['date','m','day','srkw','bon','bon_ly','bon_hist','alb','alb_ly','alb_hist']
#%%
# Function count orca reports or counts by day
def srkw_count(dat, count_orca=False):
    if count_orca:
        #print('Creating a daily average of number of orcas...')
        dat=dat.loc[:, ['no_sighted', 'date_ymd']]
        srkw_avg=dat.groupby(dat.date_ymd).mean().reset_index()
        srkw_avg=srkw_avg.rename(columns={'date_ymd':'date','no_sighted':'count'})
    else:
        #print('Creating a daily count of reports...')
        dat=dat.loc[:, ['date_ymd']]
        srkw_avg=dat['date_ymd'].value_counts().reset_index()
        srkw_avg=srkw_avg.rename(columns={'date_ymd':'count','index':'date'})
        srkw_avg=srkw_avg.sort_values(by=['date'])
    return srkw_avg
# %%
salmon_loc = pd.DataFrame(columns=['loc','lon','lat','color','size'])
salmon_loc['loc']=['Puget Sound','Bonneville Dam','Albion Test Fishery']
salmon_loc['lat']=[47.635470, 45.644456, 49.181376]
salmon_loc['lon']=[-122.457417,-121.940530, -122.567295]

# %%
# Create a color scheme and fonts
plotlycl=px.colors.qualitative.Plotly
bgcl='white'
framecl='black'
markercl='salmon'
plotly_fonts=["Arial, sans-serif", "Balto, sans-serif", "Courier New, monospace",
            "Droid Sans, sans-serif", "Droid Serif, serif",
            "Droid Sans Mono, sans-serif",
            "Gravitas One, cursive", "Old Standard TT, serif",
            "Open Sans, sans-serif",
            "PT Sans Narrow, sans-serif", "Raleway, sans-serif",
            "Times New Roman, Times, serif"]
plotfont=plotly_fonts[10]
# %%
#----------------------------------App Title------------------------------------#
app.title='Chinook Salmon Dash Board'
#----------------------------------App Layout-----------------------------------#
app.layout = html.Div(
    id="root",
    children=[
            #Header,
            html.Div(
                id="header",
                children=[
                    html.Img(id="logo", src=app.get_asset_url("logo4.png")),
                    html.H3(children="Chinook and Orca",
                            style={'textAlign': 'left',},
                    ),
                    dcc.Markdown(
                        id="description",
                        children=
                        '''
                        A dash board to monitor Chinook salmon population and Orca movement around Puget Sound                     
                        '''),
                    ],
                ),        
        dcc.Tabs(
            parent_className='custom-tabs',
            className='custom-tabs-container',
            children=[
            #----------------------------Tab 1: Salmon Time Series-----------------------------------#
                dcc.Tab(
                    label='Salmon Time Series', 
                    className='custom-tab',
                    selected_className='custom-tab--selected',
                    children=[
                        #app
                        html.Div(
                            className="app-container", 
                            children=[
                                #Left Column
                                html.Div(
                                    className="left-column", 
                                    children=[
                                        html.Div(
                                            className="salmon-container",
                                            id="salmon-container",                                           
                                            children=[
                                                html.Div(
                                                    id="drop-downs",
                                                    children=[
                                                        html.H6("Select Location"),
                                                        dcc.Dropdown(
                                                            value="Albion",
                                                            className="location-dropdown",
                                                            id="location-dropdown",
                                                            options=[
                                                                {
                                                                    "label":"Albion",
                                                                    "value":"Albion",
                                                                },
                                                                {
                                                                    "label":"Bonneville Dam",
                                                                    "value":"Bonneville Dam",
                                                                },
                                                                {
                                                                    "label":"Albion v Bonneville", 
                                                                    "value":"Albion v Bonneville"
                                                                },
                                                            ],
                                                        ),
                                                        
                                                    ],
                                                ),
                                                dcc.Graph(
                                                    className="salmon-timeseries", 
                                                    id="salmon-timeseries",
                                                                                         
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                #Right column
                                html.Div(
                                    className="right-column",
                                    id="map-container",
                                    children=[
                                        dcc.Graph(
                                            className="salmon-map",
                                            id="salmon-map",
                                            animate=False, 
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        #Footer
                        html.Div(
                            className="footer",
                            children=[
                                html.H5(
                                    [
                                        "Data Source",
                                    ]
                                ),
                                dcc.Markdown(
                                    className="credit",
                                    children=
                                    '''
                                    1. Albion Chinook test fishery is located on the lower Fraser River at Albion, BC (near Fort Langley), Canada. The fishery collects data from early April to mid-October every year. Catching per unit effort, or CPUE, is defined as catch per thousand fathom minutes. Data is retrieved from the Fisheries and Oceans Canada [report website](https://www-ops2.pac.dfo-mpo.gc.ca/fos2_Internet/Testfish/rptcsbdparm.cfm?stat=CPTFM&fsub_id=242). Read more about the Albion Chinook gill net data set, such as what size of net is used, in this document on [Albion Chinook Gillnet](https://www.pac.dfo-mpo.gc.ca/fm-gp/fraser/docs/commercial/albionchinook-quinnat-eng.html). 
                                    2. Bonneville Dam data is retrieved from Columbia Basin Research [Adult Passage Queries](https://www.cbr.washington.edu/dart/query/adult_daily). Number of adult Chinook salmon passing through the Bonneville Dam was directly monitored April to October, with video monitoring covering the other months. See [Fish Passage Center] (https://www.fpc.org/adults/Q_adults_subsite.php) for more details. 
                                    '''),
                            ],
                        ),
                    ],
                ),
                #----------------------------Tab 2: Orca Viz-----------------------------------#
                dcc.Tab(
                    label='Orcas', 
                    className='custom-tab',
                    selected_className='custom-tab--selected',
                    children=[
                        #app
                        html.Div(
                            className="app-container", 
                            children=[
                                #Left Column
                                html.Div(
                                    className="left-half-column",
                                    id="orcamap-container",
                                    children=[
                                        html.Div(
                                                id="orca-dropdowns",
                                                children=[
                                                    html.H6("Orca Sightings"),
                                                    dcc.Dropdown(
                                                            value=2022,
                                                            className="year-dropdown",
                                                            id="year-dropdown",
                                                            options=[
                                                                {
                                                                    "label":"2023",
                                                                    "value":2023,
                                                                },
                                                                {
                                                                    "label":"2022",
                                                                    "value":2022,
                                                                },
                                                                {
                                                                    "label":"2021",
                                                                    "value":2021,
                                                                },
                                                                {
                                                                    "label":"2020",
                                                                    "value":2020,
                                                                },
                                                            ],
                                                        ),
                                                    dcc.Dropdown(
                                                            value="All pods",
                                                            className="pod-dropdown",
                                                            id="pod-dropdown",
                                                            options=[
                                                                {
                                                                    "label":"L pod",
                                                                    "value":"L pod",
                                                                },
                                                                {
                                                                    "label":"K pod",
                                                                    "value":"K pod",
                                                                },
                                                                {
                                                                    "label":"J pod",
                                                                    "value":"J pod",
                                                                },
                                                                {
                                                                    "label":"All pods",
                                                                    "value":"All pods",
                                                                },
                                                            ],
                                                        ),                                                        
                                                    ],
                                                ),
                                                dcc.Graph(
                                                    className="orca-map",
                                                    id="orca-map",
                                                    animate=False,
                                                ),
                                    ],
                                ),
                                #Right column
                                html.Div(
                                    className="right-half-column", 
                                    children=[
                                        html.Div(
                                            className="salmon-orca-container",
                                            id="salmon-orca-container",                                           
                                            children=[
                                                html.H5("Number of Orcas vs Chinook"),
                                                dcc.Graph(
                                                    className="salmon-orca-timeseries", 
                                                    id="salmon-orca-timeseries",                                       
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        #Footer
                        html.Div(
                            className="footer",
                            children=[
                                html.H5(
                                    [
                                        "Data Source",
                                    ]
                                ),
                                dcc.Markdown(
                                    className="credit",
                                    children=
                                    '''
                                    1) Orca sightings data is retrieved from [Acartia](https://acartia.io/home).  
                                    2) Definition of central Salish Sea follows that of Monika Weiland in her talk talk about SRKW and Bigg's occupancy metrics.                                  
                                    '''),
                            ],
                        ),
                    ],
                ), 
            ],
        ),       
    ],
)
#-----------------------------------------------------------------------------#
#                                  Callback
# ----------------------------------------------------------------------------#
#~~~~~~~~~~~~~~~~~~~~~Salmon Time Series~~~~~~~~~~~~~~~~~~~~#
@app.callback(
    [
        Output("salmon-timeseries", "figure"),
        Output("salmon-map","figure")
    ],
    [
        Input("location-dropdown", "value"),
    ],
)
def update_salmon_timeseries(location_dropdown):
    if location_dropdown=="Bonneville Dam":
        # Define salmon time seires
        title='Bonneville Dam Adult Chinook Catch Count 3 recent years vs History'
        ylab='Count'
        xlab='Date'
        fig_salmon=go.Figure(
                data=[  #--This Year--# 
                        go.Scatter(
                        x=bonnev['date'],
                        y=bonnev['chin'+str(curyr)],
                        name=str(curyr),
                        mode='lines+markers',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[0],
                        ),
                        line = go.scatter.Line(
                                    color = plotlycl[0],
                        ),
                        opacity=0.85,     
                                ),
                        #--Last Year--# 
                        go.Scatter(
                        x=bonnev['date'],
                        y=bonnev['chin'+str(lastyr)],
                        name=str(lastyr),
                        mode='lines+markers',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[1],
                        ),
                        opacity=0.85,     
                                ),
                        #--Year before last--# 
                        go.Scatter(
                        x=bonnev['date'],
                        y=bonnev['chin'+str(twoyr)],
                        name=str(twoyr),
                        mode='lines+markers',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[2],
                        ),
                        opacity=0.85,     
                                ),
                        #--History--# 
                        go.Scatter(
                        x=bonnev['date'],
                        y=bonnev['chin_hist'],
                        name='Historical mean (1939-'+str(twoyr-1)+')',
                        mode='lines',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[3],
                        ),
                        opacity=0.85,     
                                ),
                    ],
            )
        fig_salmon.update_layout(
                paper_bgcolor=bgcl, 
                plot_bgcolor=bgcl,
                margin=dict(l=0, t=0, b=0, r=0, pad=0),
                yaxis = dict(zeroline = False,
                            title=ylab,
                            color=framecl, 
                            showgrid=False,
                ),
                xaxis = dict(zeroline = False,
                            title=xlab,
                            color=framecl,
                            showgrid=False,
                            tickmode='array',
                            tickvals=['Apr-1','May-1','Jun-1','Jul-1','Aug-1','Sep-1','Oct-1'],
                            #nticks=10,
                            tickangle=45,
                ),
                font=dict(
                    family=plotfont, 
                    size=11, 
                    color=framecl,
                ),
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=0.9,
                    xanchor="left",
                    x=0.1
                ),
                title=dict(text = title,
                                    x = 0.1,
                                    y = 0.98,
                                    xanchor =  'left',
                                    yanchor = 'top',
                                    #pad = dict(
                                    #            t = 0
                                    #           ),
                                    font = dict(
                                                #family='Courier New, monospace',
                                                size = 14,
                                                #color='#000000'
                                                )
                                    ),
            )
        fig_salmon.update_traces(connectgaps=True)
        # Define location for salmon map
        fig_salmonmap=go.Figure(
            data=go.Scattermapbox(
                lat=salmon_loc['lat'],
                lon=salmon_loc['lon'],
                mode='markers',
                marker=go.scattermapbox.Marker(
                    size=[10,20,10],
                    color=['#33C3F0','#ff6666','#ff6666'],
                    opacity=0.7,
                ),
                text=salmon_loc['loc'],
                hoverinfo='text'
            ),
            layout=dict(
                autosize=True,
                showlegend=False,
                margin=dict(l=0, r=0, t=0, b=0),
                mapbox=dict(
                accesstoken=mapbox_access_token,
                bearing=0,
                center=dict(
                    lat=47.635470,
                    lon=-122.457417
                ),
                zoom=5,
                style='light'
                ),
            ),
        )
        return fig_salmon,fig_salmonmap
    elif location_dropdown=="Albion":
        # Define salmon time seires
        title='Albion Chinook Catch Per Unit Effort (CPUE) 3 recent years vs History'
        ylab='CPUE'
        xlab='Date'
        fig_salmon=go.Figure(
                data=[  #--This Year--# 
                        go.Scatter(
                        x=albion['date'],
                        y=albion['cpue'+str(curyr)],
                        name=str(curyr),
                        mode='lines+markers',
                        #mode='lines',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[0],
                        ),
                        line = go.scatter.Line(
                                    color = plotlycl[0],
                        ),
                        opacity=0.85,     
                                ),
                        #--Last Year--# 
                        go.Scatter(
                        x=albion['date'],
                        y=albion['cpue'+str(lastyr)],
                        name=str(lastyr),
                        mode='lines+markers',
                        #mode='lines',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[1],
                        ),
                        opacity=0.85,     
                                ),
                        #--Year before last--# 
                        go.Scatter(
                        x=albion['date'],
                        y=albion['cpue'+str(twoyr)],
                        name=str(twoyr),
                        mode='lines+markers',
                        #mode='lines',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[2],
                        ),
                        opacity=0.85,     
                                ),
                        #--History--# 
                        go.Scatter(
                        x=albion['date'],
                        y=albion['cpue_hist'],
                        name='Historical mean (1980-'+str(twoyr-1)+')',
                        #mode='lines+markers',
                        mode='lines',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[3],
                        ),
                        opacity=0.85,     
                                ),
                    ],
            )
        fig_salmon.update_layout(
                paper_bgcolor=bgcl, 
                plot_bgcolor=bgcl,
                margin=dict(l=0, t=0, b=0, r=0, pad=0),
                yaxis = dict(zeroline = False,
                            title=ylab,
                            color=framecl, 
                            showgrid=False,
                ),
                xaxis = dict(zeroline = False,
                            title=xlab,
                            color=framecl,
                            showgrid=False,
                            tickmode='array',
                            tickvals=['Apr-1','May-1','Jun-1','Jul-1','Aug-1','Sep-1','Oct-1'],
                            #nticks=10,
                            tickangle=45,
                ),
                font=dict(
                    family=plotfont, 
                    size=11, 
                    color=framecl,
                ),
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=0.9,
                    xanchor="left",
                    x=0.1
                ),
                title=dict(text = title,
                                    x = 0.1,
                                    y = 0.98,
                                    xanchor =  'left',
                                    yanchor = 'top',
                                    #pad = dict(
                                    #            t = 0
                                    #           ),
                                    font = dict(
                                                #family='Courier New, monospace',
                                                size = 14,
                                                #color='#000000'
                                                )
                                    ),
            )
        fig_salmon.update_traces(connectgaps=True)
        # Define location for salmon map
        fig_salmonmap=go.Figure(
            data=go.Scattermapbox(
                lat=salmon_loc['lat'],
                lon=salmon_loc['lon'],
                mode='markers',
                marker=go.scattermapbox.Marker(
                    size=[10,10,20],
                    color=['#33C3F0','#ff6666','#ff6666'],
                    opacity=0.7,
                ),
                text=salmon_loc['loc'],
                hoverinfo='text'
            ),
            layout=dict(
                autosize=True,
                showlegend=False,
                margin=dict(l=0, r=0, t=0, b=0),
                mapbox=dict(
                accesstoken=mapbox_access_token,
                bearing=0,
                center=dict(
                    lat=47.635470,
                    lon=-122.457417
                ),
                zoom=5,
                style='light'
                ),
            ),
        )
        return fig_salmon, fig_salmonmap
    elif location_dropdown=="Albion v Bonneville":
        # Define salmon time seires
        title='Albion Chinook vs Bonneville Dam'
        ylab='CPUE'
        xlab='Date'
        fig_salmon = make_subplots(specs=[[{"secondary_y": True}]])
        fig_salmon.add_trace(
                go.Scatter(
                        x=srkw_curyr_count['date'],
                        y=srkw_curyr_count['alb'],
                        name='Albion'+str(curyr),
                        mode='lines+markers',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[0],
                        ),
                        line = go.scatter.Line(
                                    color = plotlycl[0],
                        ),
                        opacity=0.85,     
                                ),
            secondary_y=False,
        )
        if today.month<=4:
            fig_salmon.add_trace(
                go.Scatter(
                        x=srkw_curyr_count['date'],
                        y=srkw_curyr_count['alb_ly'],
                        name='Albion'+str(curyr-1),
                        mode='lines+markers',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[1],
                        ),
                        line = go.scatter.Line(
                                    color = plotlycl[1],
                        ),
                        opacity=0.85,     
                                ),
            secondary_y=False,
            )
        fig_salmon.add_trace(
                go.Scatter(
                        x=srkw_curyr_count['date'],
                        y=srkw_curyr_count['alb_hist'],
                        name='Albion historical mean',
                        mode='lines',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[2],
                        ),
                        line = go.scatter.Line(
                                    color = plotlycl[2],
                        ),
                        opacity=0.85,     
                                ),
            secondary_y=False,
        )
        fig_salmon.add_trace(
            go.Scatter(
                        x=srkw_curyr_count['date'],
                        y=srkw_curyr_count['bon'],
                        name='Bonneville'+str(curyr),
                        mode='lines+markers',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[3],
                        ),
                        line = go.scatter.Line(
                                    color = plotlycl[3],
                        ),
                        opacity=0.85,     
                                ),
            secondary_y=True,
        )
        if today.month<=4:
            fig_salmon.add_trace(
            go.Scatter(
                        x=srkw_curyr_count['date'],
                        y=srkw_curyr_count['bon_ly'],
                        name='Bonneville'+str(curyr-1),
                        mode='lines+markers',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[4],
                        ),
                        line = go.scatter.Line(
                                    color = plotlycl[4],
                        ),
                        opacity=0.85,     
                                ),
            secondary_y=True,
            )
        fig_salmon.add_trace(
            go.Scatter(
                        x=srkw_curyr_count['date'],
                        y=srkw_curyr_count['bon_hist'],
                        name='Bonneville historical mean',
                        mode='lines',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[5],
                        ),
                        line = go.scatter.Line(
                                    color = plotlycl[5],
                        ),
                        opacity=0.85,     
                                ),
            secondary_y=True,
        )
        fig_salmon.update_yaxes(title_text="CPUE (Albion)", secondary_y=False)
        fig_salmon.update_yaxes(title_text="Count (Bonneville)", secondary_y=True)

        fig_salmon.update_layout(
                paper_bgcolor=bgcl, 
                plot_bgcolor=bgcl,
                margin=dict(l=0, t=0, b=0, r=0, pad=0),
                yaxis = dict(zeroline = False,
                            color=framecl, 
                            showgrid=False,
                ),
                xaxis = dict(zeroline = False,
                            title=xlab,
                            color=framecl,
                            showgrid=False,
                            tickmode='array',
                            tickvals=['Apr-1','May-1','Jun-1','Jul-1','Aug-1','Sep-1','Oct-1'],
                            #nticks=10,
                            tickangle=45,
                ),
                font=dict(
                    family=plotfont, 
                    size=11, 
                    color=framecl,
                ),
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=0.9,
                    xanchor="left",
                    x=0.1
                ),
                title=dict(text = title,
                                    x = 0.1,
                                    y = 0.98,
                                    xanchor =  'left',
                                    yanchor = 'top',
                                    #pad = dict(
                                    #            t = 0
                                    #           ),
                                    font = dict(
                                                #family='Courier New, monospace',
                                                size = 14,
                                                #color='#000000'
                                                )
                                    ),
            )
        fig_salmon.update_traces(connectgaps=True)
        # Define location for salmon map
        fig_salmonmap=go.Figure(
            data=go.Scattermapbox(
                lat=salmon_loc['lat'],
                lon=salmon_loc['lon'],
                mode='markers',
                marker=go.scattermapbox.Marker(
                    size=[10,20,20],
                    color=['#33C3F0','#ff6666','#ff6666'],
                    opacity=0.7,
                ),
                text=salmon_loc['loc'],
                hoverinfo='text'
            ),
            layout=dict(
                autosize=True,
                showlegend=False,
                margin=dict(l=0, r=0, t=0, b=0),
                mapbox=dict(
                accesstoken=mapbox_access_token,
                bearing=0,
                center=dict(
                    lat=47.635470,
                    lon=-122.457417
                ),
                zoom=5,
                style='light'
                ),
            ),
        )
        return fig_salmon, fig_salmonmap

#~~~~~~~~~~~~~~~~~~~~~Orca Map~~~~~~~~~~~~~~~~~~~~#
@app.callback(
    Output("orca-map", "figure"),
    [
        Input("pod-dropdown", "value"),
        Input("year-dropdown","value")
    ],
)
def update_orca_map(pod,year):
    srkwc=pd.read_csv(acartia_path+"srkw_"+str(year)+".csv")
    srkwc['date2']=pd.to_datetime(srkwc['date_ymd'],format='%Y-%m-%d', errors='coerce')
    srkwc['day_of_year']=srkwc['date_ymd'].apply(lambda x: pd.Period(x, freq='D').day_of_year)
    srkwc_k=srkwc[srkwc.K==1].reset_index()
    srkwc_l=srkwc[srkwc.L==1].reset_index()
    srkwc_j=srkwc[srkwc.J==1].reset_index()

    if pod=="L pod":
        srkw_dat=srkwc_l
    elif pod=="K pod":
        srkw_dat=srkwc_k
    elif pod=="J pod":
        srkw_dat=srkwc_j
    elif pod=="All pods":
        srkw_dat=srkwc[srkwc.sum_jkl>=1]
    fig_orcamap = go.Figure()
    fig_orcamap.add_trace(go.Scattermapbox(
            lat=srkw_dat['latitude'],
            lon=srkw_dat['longitude'],
            mode='markers',
            marker=go.scattermapbox.Marker(
                color=srkw_dat.day_of_year,
                size=7,
                colorscale='Viridis',
                opacity=0.75,
                showscale=True,
                colorbar=dict(
                title='Day of the year',
                thickness=20,
                titleside='right',
                outlinecolor='rgba(68,68,68,0)',
                ticks='outside',
                ticklen=3,),     
            ),
            text=srkw_dat['created']+'<br>'+srkw_dat['data_source_comments'],
            hoverinfo='text'
        ))
    fig_orcamap.update_layout(
        autosize=True,
        showlegend=False,
        uirevision=True,
        margin=dict(l=0, r=0, t=0, b=0),
        mapbox=dict(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=dict(
                lat=47.635470,
                lon=-122.457417
            ),
            zoom=6,
            style='light'
        ),
    )
    return fig_orcamap

#~~~~~~~~~~~~~~~~~~~~~Orca Time series~~~~~~~~~~~~~~~~~~~~#
@app.callback(
    Output("salmon-orca-timeseries", "figure"),
    [
        Input("pod-dropdown", "value"),
        Input("year-dropdown","value")
    ],
)
def update_orca_lines(pod,year):
    srkwc=pd.read_csv(acartia_path+"srkw_"+str(year)+".csv")
    srkwc['date2']=pd.to_datetime(srkwc['date_ymd'],format='%Y-%m-%d', errors='coerce')
    srkwc['day_of_year']=srkwc['date_ymd'].apply(lambda x: pd.Period(x, freq='D').day_of_year)
    # Define the north and south puget sound latitude
    entry_lat=48.19437
    srkwc['north_puget_sound']=srkwc['latitude'].apply(lambda x: 1 if x>entry_lat else 0)
    srkwc_k=srkwc[srkwc.K==1].reset_index()
    srkwc_l=srkwc[srkwc.L==1].reset_index()
    srkwc_j=srkwc[srkwc.J==1].reset_index()

    if pod=="L pod":
        srkw_dat=srkwc_l
    elif pod=="K pod":
        srkw_dat=srkwc_k
    elif pod=="J pod":
        srkw_dat=srkwc_j
    elif pod=="All pods":
        srkw_dat=srkwc[srkwc.sum_jkl>=1]

    srkwc_north=srkw_dat[srkw_dat['north_puget_sound']==1]
    srkwc_north_avg=srkw_count(srkwc_north, count_orca=True)
    srkwc_south=srkw_dat[srkw_dat['north_puget_sound']==0]
    srkwc_south_avg=srkw_count(srkwc_south, count_orca=True)

    srkw_curyr_count=srkwc[['m','day','date']]
    srkw_curyr_count=srkw_curyr_count['date'].value_counts().reset_index()
    srkw_curyr_count=srkw_curyr_count.rename(columns={'date':'count', 'index':'date'})
    srkw_curyr_count['day']=srkw_curyr_count['date'].apply(lambda x: x.split('-')[1])
    srkw_curyr_count['day_int']=srkw_curyr_count['day'].astype("int")
    srkw_curyr_count['mon']=srkw_curyr_count['date'].apply(lambda x: x.split('-')[0])
    srkw_curyr_count['m']=srkw_curyr_count['mon'].apply(lambda x: dt.strptime(x, '%b').month)
    srkw_curyr_count['m2']=srkw_curyr_count['m'].astype('float')
    srkw_curyr_count['day2']=srkw_curyr_count['day'].astype('float')
    srkw_curyr_count=srkw_curyr_count.sort_values(by=['m2','day2'])

    fig_orcaline = make_subplots(rows=3, cols=1)
    fig_orcaline.append_trace(
        go.Scatter(
            x=srkwc_north_avg['date'],
            y=srkwc_north_avg['count'],
            mode="markers",
            name="Central Salish Sea", 
            hovertemplate='%{x}'+': %{y}',
            marker=go.scatter.Marker(color=px.colors.sequential.Viridis[0]),
            ),
    row=1, col=1)
    fig_orcaline.append_trace(
        go.Scatter(
                x=srkwc_south_avg['date'],
                y=srkwc_south_avg['count'],
                mode="markers",
                name="Puget Sound", 
                hovertemplate='%{x}'+': %{y}',
                marker=go.scatter.Marker(color=px.colors.sequential.Viridis[-1]),
            ),
    row=1, col=1
    )
    """ fig_orcaline.append_trace(
        go.Scatter(
        x=srkw_curyr_count['date'],
        y=srkw_curyr_count['count'],
        name='Orca'+str(year),
        mode='lines+markers',
        hovertemplate='%{x}'+':%{y}',
        marker = go.scatter.Marker(
            color = plotlycl[0],
        ),
        line = go.scatter.Line(
            color = plotlycl[0],
        ),
        opacity=0.85,
        ), 
        row=1, col=1
    ) """

    fig_orcaline.append_trace(
        go.Scatter(
            x=albion['date'],
            y=albion['cpue'+str(year)],
            name='Albion'+str(year),
            mode='lines+markers',
            hovertemplate='%{x}'+':%{y}',
            marker = go.scatter.Marker(
                color = px.colors.sequential.Viridis[7],
            ),
            line = go.scatter.Line(
                color = px.colors.sequential.Viridis[7],
            ),
            opacity=0.85,), 
    row=2, col=1)
    fig_orcaline.append_trace(
        go.Scatter(
            x=bonnev['date'],
            y=bonnev['chin'+str(year)],
            name='Bonneville'+str(year),
            mode='lines+markers',
            hovertemplate='%{x}'+':%{y}',
            marker = go.scatter.Marker(
                color = px.colors.sequential.Viridis[4],
            ),
            line = go.scatter.Line(
                color = px.colors.sequential.Viridis[4],
            ),
            opacity=0.85,),
    row=3, col=1)


    fig_orcaline.update_layout(
        paper_bgcolor=bgcl,
        plot_bgcolor=bgcl,
        margin=dict(t=0, r=0, b=0, l=0, pad=0,),
        yaxis = dict(zeroline = False,
            title='# of orcas',
            color=framecl, 
            showgrid=False,                                
            ),
        xaxis = dict(zeroline = False,
            color=framecl,
            showgrid=False,
            ),
            font=dict(
                family=plotfont, 
                size=9.5, 
                color=framecl,
            ),
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1.2,
                xanchor="left",
                x=0.1
            ),
        )
    fig_orcaline.update_yaxes(title_text='Chinook CPUE', row=2, col=1)
    fig_orcaline.update_yaxes(title_text='Chinook Count',  row=3, col=1)
    fig_orcaline.update_xaxes(tickmode='array',
                        tickvals=['2022-01-01','2022-02-01','2022-03-01','2022-04-01','2022-05-01','2022-06-01','2022-07-01','2022-08-01','2022-09-01','2022-10-01','2022-11-01','2022-12-01',],
                        ticktext=['Jan-1','Feb-1','Mar-1','Apr-1','May-1','Jun-1','Jul-1','Aug-1','Sept-1','Oct-1','Nov-1','Dec-1'],
                        #tickvals=['Jan-1','Feb-1','Mar-1','Apr-1','May-1','Jun-1','Jul-1','Aug-1','Sep-1','Oct-1','Nov-1','Dec-1'],
                        #nticks=12,
                        tickangle=45, row=1, col=1)
    fig_orcaline.update_xaxes(tickmode='array',
                        tickvals=['Jan-1','Feb-1','Mar-1','Apr-1','May-1','Jun-1','Jul-1','Aug-1','Sep-1','Oct-1','Nov-1','Dec-1'],
                        #nticks=12,
                        tickangle=45, row=2, col=1)
    fig_orcaline.update_xaxes(tickmode='array',
                        tickvals=['Jan-1','Feb-1','Mar-1','Apr-1','May-1','Jun-1','Jul-1','Aug-1','Sep-1','Oct-1','Nov-1','Dec-1'],
                        #nticks=12,
                        tickangle=45,  row=3, col=1)
    fig_orcaline.update_traces(connectgaps=True)
    return fig_orcaline

if __name__ == '__main__':
    app.run_server(debug=True)