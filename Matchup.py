import streamlit as st
import requests
import numpy as np
import pandas as pd
from database import Database

import utils

database = Database()

st.set_page_config(
    page_title='Fantasy Disc Golf',
    layout='wide'
)

st.title("Fantasy Disc Golf")

controls = st.columns([.3,.7])
with controls[0]:
    league_name = st.selectbox('League', [l['League Name'] for l in database.get_leagues()])
with controls[1]:
    event_name = st.selectbox('Event', database.EVENTS.keys())

if event_name is not None and league_name is not None:

    results = database.get_event_results(event_name, league_name)

    tabs = st.tabs([t['Owner'] for t in database.get_teams(league_name)])
    for i, team in enumerate(database.get_teams(league_name)):

        with tabs[i]:
            results.index = results.index.astype(str)
            df = results.loc[team['Players']].copy()
            total = df.sum(0)
            total['Name'] = 'Total'
            total = total.to_frame().T
            df = pd.concat([total, df])
            style = df.style.format(precision=1).hide(axis=0)
            st.write(style.to_html(), unsafe_allow_html=True)
