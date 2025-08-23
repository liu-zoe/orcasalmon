## Project Name: Orcasound Salmon
### Program Name: app.py
### Purpose: To make a dash board for the Chinook salmon data
##### Date Created: Dec 14th 2024

import os
from os.path import join as pjoin
import pathlib
from datetime import date
import glob 
import pandas as pd
pd.options.mode.chained_assignment = None #suppress chained assignment 

import numpy as np
import dash
from dash import dcc
from dash import html 
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.express as px
from plotly.express.colors import sample_colorscale
from apputils import (load_albion, load_bon, load_wash,
                      calendar_template, create_lagged, 
                      acartia_map_preproc, twm_map_preproc, 
                      peak_srkw,
                      apeak_df, srkw_peak_df)

#--------------------------Load And Process Data----------------------------#
APP_PATH = str(pathlib.Path(__file__).parent.resolve())
try: 
    mapbox_access_token = open(pjoin(APP_PATH,"mapbox_token.txt")).read() #For debugging locally
except:
    mapbox_access_token = os.environ.get('MAPBOX_TOKEN') #For deployment

#Get dates
today=date.today()
todaystr=str(today)
curyr=today.year
# curyr=2024
lastyr=curyr-1
twoyr=curyr-2
ayl=[y for y in range(1980, curyr+1)] #year list for Albion
byl=[y for y in range(1939, curyr+1)] #year list for Bonneville Dam
twmyl=[y for y in range(1976, 2022)] #year list for TWM data
#Define data path
fos_path=pjoin(APP_PATH,'data/foschinook/')
bon_path=pjoin(APP_PATH,'data/bonchinook/')
lakewash_path=pjoin(APP_PATH,'data/lakewash/')
acartia_path=pjoin(APP_PATH, 'data/acartia/')
twm_path=pjoin(APP_PATH, 'data/twm_data/')
srkw_path=pjoin(APP_PATH, 'data/')
#Test folder
try:
  subfolders = glob.glob(f"{srkw_path}/**/", recursive=True)
  with open(pjoin(srkw_path, "test.log")) as logf:
    for folder_path in subfolders:
      subfolder_name = os.path.basename(os.path.normpath(folder_path))
      if subfolder_name: # Ensure it's not an empty string if base_directory is matched
        logf.write(f"{subfolder_name}\n")      
except Exception as e:
  print(e) 
  
#Load Bonneville data
bonnev=load_bon(bon_path)

# Create calendar dataframes 
cal=calendar_template(bonnev)
calleap=calendar_template(bonnev, leap=True)

#Load Albion data
albion, albsum=load_albion(fos_path)
albion=calleap.merge(albion, how='left', on=['m','day'])
# Create a combined data of Albion and Bonneville and create a lag 
lagged=create_lagged(curyr, albion, bonnev, 10, 10)

# Load Lake Washington data
wash=load_wash(lakewash_path)

twm_map_data=twm_map_preproc(2017, twm_path, "All pods")
acartia_map_data=acartia_map_preproc(2023, acartia_path)

# Calculating peak values of Chinook at Albion
apeak, apeak95=apeak_df(curyr, fos_path, bon_path)
# Calculating peak values of Orca sightings 
srkw_cs_peak, srkw_cs_peak95=srkw_peak_df(curyr, twm_path, acartia_path)

srkw_cs_pv, srkw_cs_pdt, srkw_cs_pdy, srkw_cs_df=peak_srkw(curyr, twm_path, acartia_path, src="both", loc="central salish")

# Load The SRKW Population Data
srkwdata=pd.read_csv(pjoin(APP_PATH, "data/SRKW.csv"))
srkwdata_all=srkwdata[['year','JKL']]
srkwdata_all=srkwdata_all.rename(columns={"JKL":"SRKW"})
srkwdata_j=srkwdata[['year','J']]
srkwdata_j=srkwdata_j.rename(columns={"J":"SRKW"})
srkwdata_k=srkwdata[['year','K']]
srkwdata_k=srkwdata_k.rename(columns={"K":"SRKW"})
srkwdata_l=srkwdata[['year','L']]
srkwdata_l=srkwdata_l.rename(columns={"L":"SRKW"})

# Define path to salmon map image
salmon_map_path = 'assets/diagram_of_locations_v2.png'

# Create a color schemes and fonts
plotlycl=px.colors.qualitative.Plotly
clr12pt=np.linspace(0.083,1,12)
#clr12pt=[0.083,0.167,0.25,0.333,0.417,0.5,0.583,0.667,0.75,0.833,0.917,1]
viri12cl=sample_colorscale('viridis', samplepoints=clr12pt)
viri12=[[clr12pt[i], viri12cl[i]] for i in range(12)]
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
                    html.A(id="github-link",children=[
                        html.Img(id="github", src=app.get_asset_url("icone-github-grise.png"),
                        ),
                    ], href='https://github.com/liu-zoe/orcasalmon', target="_blank"),
                    html.A(id="logo-link",
                           children=[
                        html.Img(id="logo", src=app.get_asset_url("wordlogo-seagreen.png"),
                        style={'height':'20%', 'width':'20%'}
                        ),        
                    ], href="https://www.orcasound.net", target="_blank"),
                
                    html.H3(children="Chinook and Orca",
                            style={'textAlign': 'left',},
                    ),
                    dcc.Markdown(
                        id="description",
                        children=
                        '''
                        A dash board to monitor Chinook salmon population and Orca movement around Puget Sound and Central Salish Sea                    
                        '''),
                    ],
                ),        
        dcc.Tabs(
            parent_className='custom-tabs',
            className='custom-tabs-container',
            children=[
            #----------------------------Tab 1: Salmon Time Series-----------------------------------#
                dcc.Tab(
                    label='Chinook Salmon', 
                    className='custom-tab',
                    selected_className='custom-tab--selected',
                    children=[
                        #app
                        html.Div(
                            className="app-container", 
                            children=[
                                #Salmon Map column
                                html.Div(
                                    className="left-column",
                                    id="graph-container",
                                    children=[
                                        html.H6("Salish Sea and Puget Sound", 
                                                ),
                                        html.Img(id="salmon-static-map",
                                                src=salmon_map_path, 
                                                 ),
                                    ],
                                ),       
                                #Salmon time series Column
                                html.Div(
                                    className="right-column", 
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
                                                            value="Albion v Bonneville",
                                                            className="location-dropdown",
                                                            id="location-dropdown",
                                                            options=[
                                                                {
                                                                    "label":"Albion v Bonneville", 
                                                                    "value":"Albion v Bonneville"
                                                                },
                                                                {
                                                                    "label":"Albion",
                                                                    "value":"Albion",
                                                                },
                                                                {
                                                                    "label":"Bonneville Dam",
                                                                    "value":"Bonneville Dam",
                                                                },
                                                                {
                                                                    "label":"Lake Washington",
                                                                    "value":"Lake Washington",
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
                            ],
                        ),
                        #Footer
                        html.Div(
                            className="footer",
                            children=[
                                html.H6(
                                    children=["Data Source",], 
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
                    label='Southern Resident Orca', 
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
                                                    html.H6("Southern Resident Orca Sightings"),
                                                    dcc.Dropdown(
                                                            value=2025,
                                                            className="year-dropdown",
                                                            id="year-dropdown",
                                                            options=[
                                                                {"label":"2025","value":2025,},
                                                                {"label":"2024","value":2024,},
                                                                {"label":"2023","value":2023,},
                                                                {"label":"2022","value":2022,},
                                                                {"label":"2021","value":2021,},
                                                                {"label":"2020","value":2020,},
                                                                {"label":"2019","value":2019,},
                                                                {"label":"2018","value":2018,},
                                                                {"label":"2017","value":2017,},
                                                                {"label":"2016","value":2016,},
                                                                {"label":"2015","value":2015,},
                                                                {"label":"2014","value":2014,},
                                                                {"label":"2013","value":2013,},
                                                                {"label":"2012","value":2012,},
                                                                {"label":"2011","value":2011,},
                                                                {"label":"2010","value":2010,},
                                                                {"label":"2009","value":2009,},
                                                                {"label":"2008","value":2008,},
                                                                {"label":"2007","value":2007,},
                                                                {"label":"2006","value":2006,},
                                                                {"label":"2005","value":2005,},
                                                                {"label":"2004","value":2004,},
                                                                {"label":"2003","value":2003,},
                                                                {"label":"2002","value":2002,},
                                                                {"label":"2001","value":2001,},                                                                
                                                                {"label":"2000","value":2000,},
                                                                {"label":"1999","value":1999,},
                                                                {"label":"1998","value":1998,},
                                                                {"label":"1997","value":1997,},
                                                                {"label":"1996","value":1996,},
                                                                {"label":"1995","value":1995,},
                                                                {"label":"1994","value":1994,},
                                                                {"label":"1993","value":1993,},
                                                                {"label":"1992","value":1992,},
                                                                {"label":"1991","value":1991,},
                                                                {"label":"1990","value":1990,},
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
                                                html.H5("Why is Chinook Salmon important to Southern Resident Orcas?"),
                                                html.P("The Southern Resident killer whales, an iconic population of orcas found in the Pacific Northwest, face a critical threat to their survival due to the lack of chinook salmon. These majestic creatures, known for their intelligence and close-knit social structure, heavily rely on chinook salmon as their primary food source. However, the decline in chinook populations, caused by various factors including habitat degradation, overfishing, and dam construction, has left the Southern Resident orcas in a precarious state. With insufficient access to their preferred prey, these magnificent marine mammals struggle to meet their nutritional needs, resulting in malnutrition and overall population decline."),
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
                                html.H6(
                                    children=[
                                        "Data Source",
                                    ],
                                    style={
                                        "margin-top":"1.8rem"
                                        },
                                ),
                                dcc.Markdown(
                                    className="credit",
                                    children=
                                    '''
                                    1. Orca geolocation data are retrieved from [Acartia](https://acartia.io/home) (2018-present) and [The Whale Museum](https://whalemuseum.org/) (1990-2021). 
                                    2. Definition of central Salish Sea follows that of Monika Weiland in her talk about SRKW and Bigg's occupancy metrics.                                  
                                    3. The top time series chart depicting peak Chinook CPUE and Orca sightings illustrate observed data without any modeling. Lighter-shaded data points represent days when the observed Chinook CPUE or Orca sightings were in the top 95 percentile, while darker-shaded data points represent days when they reached their highest levels of the year.
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
    Output("salmon-timeseries", "figure"),
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
                data=[  
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
                        #--This Year--# 
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
                            tickvals=['Mar-1','Apr-1','May-1','Jun-1','Jul-1','Aug-1','Sep-1','Oct-1','Nov-1','Dec-1'],
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
    elif location_dropdown=="Albion":
        # Define salmon time seires
        title='Albion Chinook Catch Per Unit Effort (CPUE) 3 recent years vs History'
        ylab='CPUE'
        xlab='Date'
        fig_salmon=go.Figure(
                data=[  
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
                        #--This Year--# 
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
                                    font = dict(
                                                #family='Courier New, monospace',
                                                size = 14,
                                                #color='#000000'
                                                )
                                    ),
            )
        fig_salmon.update_traces(connectgaps=True)
    elif location_dropdown=="Lake Washington":
        # Define salmon time seires
        title='Lake Washington Chinook Count'
        ylab='Count'
        xlab='Date'
        fig_salmon=go.Figure(
                data=[  
                        # #--Year before last--# 
                        # go.Scatter(
                        # x=bonnev['date'],
                        # y=bonnev['chin'+str(twoyr)],
                        # name=str(twoyr),
                        # mode='lines+markers',
                        # hovertemplate='%{x}'+':%{y}',
                        # marker = go.scatter.Marker(
                        #             color = plotlycl[2],
                        # ),
                        # opacity=0.85,     
                        #         ),
                        #--Last Year--# 
                        go.Scatter(
                        x=wash['date'],
                        y=wash['chin'+str(lastyr)],
                        name=str(lastyr),
                        mode='lines+markers',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[1],
                        ),
                        opacity=0.85,     
                                ),
                        # #--This Year--# 
                        # go.Scatter(
                        # x=bonnev['date'],
                        # y=bonnev['chin'+str(curyr)],
                        # name=str(curyr),
                        # mode='lines+markers',
                        # hovertemplate='%{x}'+':%{y}',
                        # marker = go.scatter.Marker(
                        #             color = plotlycl[0],
                        # ),
                        # line = go.scatter.Line(
                        #             color = plotlycl[0],
                        # ),
                        # opacity=0.85,     
                        #         ),
                        # #--History--# 
                        # go.Scatter(
                        # x=bonnev['date'],
                        # y=bonnev['chin_hist'],
                        # name='Historical mean (1939-'+str(twoyr-1)+')',
                        # mode='lines',
                        # hovertemplate='%{x}'+':%{y}',
                        # marker = go.scatter.Marker(
                        #             color = plotlycl[3],
                        # ),
                        # opacity=0.85,     
                        #         ),
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
                            tickvals=['Mar-1','Apr-1','May-1','Jun-1','Jul-1','Aug-1','Sep-1','Oct-1','Nov-1','Dec-1'],
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
    elif location_dropdown=="Albion v Bonneville":
        # Define salmon time seires
        if today.month<=4:
            albbon=create_lagged(curyr, albion, bonnev, 0, 0)
            albbon_ly=create_lagged(lastyr, albion, bonnev, 0, 0)
            albbon=albbon.merge(albbon_ly[['m','day','chin'+str(lastyr),'cpue'+str(lastyr)]], how='left',on=['m','day'])
        else:
            albbon=create_lagged(curyr, albion, bonnev, 0, 0)
        title='Albion Chinook vs Bonneville Dam'
        ylab='CPUE'
        xlab='Date'
        fig_salmon = make_subplots(specs=[[{"secondary_y": True}]])
        fig_salmon.add_trace(
                go.Scatter(
                        x=albbon['date'],
                        y=albbon['cpue'+str(curyr)],
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
                        x=albbon['date'],
                        y=albbon['cpue'+str(lastyr)],
                        name='Albion'+str(lastyr),
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
                        x=albbon['date'],
                        y=albbon['cpue_hist'],
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
                        x=albbon['date'],
                        y=albbon['chin'+str(curyr)],
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
                        x=albbon['date'],
                        y=albbon['chin'+str(lastyr)],
                        name='Bonneville'+str(lastyr),
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
                        x=albbon['date'],
                        y=albbon['chin_hist'],
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
                            tickvals=['Jan-1','Feb-1','Mar-1','Apr-1','May-1','Jun-1','Jul-1','Aug-1','Sep-1','Oct-1','Nov-1','Dec-1'],
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
    return fig_salmon

#~~~~~~~~~~~~~~~~~~~~~Orca Map~~~~~~~~~~~~~~~~~~~~#
@app.callback(
    Output("orca-map", "figure"),
    [
        Input("pod-dropdown", "value"),
        Input("year-dropdown","value")
    ],
)
#%%
def update_orca_map(pod,year):
    if year>2021:      
        srkw_dat=acartia_map_preproc(year, acartia_path, pod)
    elif year>2017:
        srkw_dat0=acartia_map_preproc(year, acartia_path, pod)
        srkw_dat1=twm_map_preproc(year, twm_path, pod)
        srkw_dat=pd.concat([srkw_dat0, srkw_dat1])
    else:
        srkw_dat=twm_map_preproc(year, twm_path, pod)
    
    # create an empty dataset with all months of the year
    empty_srkw_dat=pd.DataFrame()
    empty_srkw_dat['m']=list(range(1,13))
    empty_srkw_dat['year']=year
    empty_srkw_dat['mon_frac']=empty_srkw_dat['m'].apply(lambda x: clr12pt[int(x)-1])

    # find the current months if year = curyear
    if year==curyr:
        max_m=max(srkw_dat.m)
        append_dat=empty_srkw_dat[empty_srkw_dat['m']>max_m]
        srkw_dat=pd.concat([srkw_dat, append_dat])
    else:
        srkw_dat=pd.concat([srkw_dat, empty_srkw_dat])
    fig_orcamap = go.Figure()
    fig_orcamap.add_trace(go.Scattermapbox(
            lat=srkw_dat['latitude'],
            lon=srkw_dat['longitude'],
            mode='markers',
            marker=go.scattermapbox.Marker(
                color=srkw_dat.mon_frac,
                size=7,
                colorscale=viri12cl,
                opacity=0.75,
                showscale=True,
                colorbar=dict(
                    title='Month',
                    thickness=20,
                    titleside='right',
                    outlinecolor='rgba(68,68,68,0)',
                    ticks='outside',
                    ticklen=3,
                    tickmode='array',
                    tickvals=clr12pt,
                    ticktext=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"
                    ],
                ),     
            ),
            text=srkw_dat['tag'],
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
#%%
#~~~~~~~~~~~~~~~~~~~~~Orca Time series~~~~~~~~~~~~~~~~~~~~#
@app.callback(
    Output("salmon-orca-timeseries", "figure"),
    [
        Input("pod-dropdown", "value"),
    ],
)
def update_orca_lines(pod):
    if pod=="All pods":
        pod_tag=""
        srkw=srkwdata_all
    elif pod=="J pod":
        pod_tag="[J]"
        srkw=srkwdata_j
    elif pod=="K pod":
        pod_tag="[K]"
        srkw=srkwdata_k
    elif pod=="L pod":
        pod_tag="[L]"
        srkw=srkwdata_l 

    fig_peak = make_subplots(rows=2,cols=1,
                         subplot_titles=['','Orca Population'],
                         row_heights=[0.7,0.3],
    specs=[[{"secondary_y": False}],[{"secondary_y": True}]]
    )
    fig_peak.add_trace(
            go.Scatter(
                x=srkw_cs_peak['year'],
                y=srkw_cs_peak['peakday'],
                name=f'Orca sightings peak day {pod_tag}',
                mode='markers',
                hovertemplate='%{y} day'+', %{x}',
                marker = go.scatter.Marker(
                            color = plotlycl[0],
                            symbol="triangle-ne",
                    ),
                    opacity=0.85, 
            ),row=1, col=1,
    )
    fig_peak.add_trace(
        go.Scatter(
            x=srkw_cs_peak95['year'],
            y=srkw_cs_peak95['peakday'],
            name=f'Orca sightings peak day {pod_tag}',
            mode='markers',
            hovertemplate='%{y} day'+', %{x}',
            marker = go.scatter.Marker(
                        color = plotlycl[0],
                        symbol="triangle-ne",
                ),
            showlegend=False,
            opacity=0.25,
        ),row=1, col=1,
    )
    fig_peak.add_trace(
            go.Scatter(
                x=apeak['year'],
                y=apeak['peakday'],
                name='Chinook at Albion peak day',
                mode='markers',
                hovertemplate='%{y} day'+', %{x}',
                marker = go.scatter.Marker(
                            color = plotlycl[1],
                            symbol="triangle-ne", 
                    ),
                    opacity=0.85, 
            ),row=1, col=1,
    )
    fig_peak.add_trace(
        go.Scatter(
            x=apeak95['year'],
            y=apeak95['peakday'],
            name='Chinook at Albion peak day',
            mode='markers',
            hovertemplate='%{y} day'+', %{x}',
            marker = go.scatter.Marker(
                        color = plotlycl[1],
                        symbol="triangle-ne", 
                ),
            opacity=0.25,
            showlegend=False,
        ),row=1, col=1,
    )

    #---SRKW Population---#
    fig_peak.add_trace(
            go.Scatter(
                x=srkw['year'],
                y=srkw['SRKW'],
                name=f"Orca Number {pod}",
                mode='lines+markers',
                hovertemplate='%{x}'+':%{y}',
                marker = go.scatter.Marker(
                            color = plotlycl[0],
                            symbol="star",
                    ),
                line = go.scatter.Line(
                            color = plotlycl[0],
                            dash='dot',
                    ),
                    opacity=0.85, 
            ), secondary_y=False,row=2, col=1,
    )
    #---Albion Salmon Sum---#
    fig_peak.add_trace(
        go.Scatter(
                x=albsum['year'],
                y=albsum['alb_cpue'], 
                name='Chinook at Albion',
                mode='lines+markers',
                hovertemplate='%{x}'+':%{y}',
                marker = go.scatter.Marker(
                            color = plotlycl[1],
                            symbol="star",
                    ),
                line = go.scatter.Line(
                            color = plotlycl[1],
                            dash="dot",
                    ),
                    opacity=0.85, 
            ),secondary_y=True,row=2, col=1,
    )

    fig_peak.update_yaxes(title_text="Peak day of the year", tickvals=list(range(150,300,50)), range=[140, 300], row=1, col=1)
    fig_peak.update_yaxes(title_text="Number of Orca", row=2, col=1, secondary_y=False)
    fig_peak.update_yaxes(title_text="Albion Chinook CPUE", row=2, col=1, secondary_y=True)
    fig_peak.update_xaxes(title_text="Year",tickvals=list(range(1990,curyr,5)),range=[1989, 2024], row=1, col=1)
    fig_peak.update_xaxes(title_text="Year",tickvals=list(range(1990,curyr,5)),range=[1989, 2024], row=2, col=1)

    fig_peak.update_layout(
            paper_bgcolor=bgcl, 
            plot_bgcolor=bgcl,
            margin=dict(l=0, t=0, b=0, r=0, pad=0),
            yaxis = dict(zeroline = False,
                        color=framecl, 
                        showgrid=False,
            ),
            xaxis = dict(zeroline = False,
                        color=framecl,
                        showgrid=False,
            ),
            font=dict(
                family=plotfont, 
                size=11, 
                color=framecl,
            ),
            legend=dict(
                y=0.9,
            ),
            title=dict(text = "Peak day of Chinook Volume at Albion and Southern Resident Orca Sightings in Central Salish Sea",
                                x = 0.02,
                                y = 1,
                                xanchor = 'left',
                                yanchor = 'top',
                                pad = dict(
                                           t = 1
                                          ),
                                font = dict(
                                            family='Arial, sans-serif',
                                            size = 16,
                                            #color='#000000'
                                            )
                                ),
        )
    return fig_peak

if __name__ == '__main__':
    app.run_server(debug=True)
