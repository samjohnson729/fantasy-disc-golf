import json

import streamlit as st
import pandas as pd

from database import Database
import utils

database = Database()

st.title('Draft')

league_name = st.selectbox('League', [l['League Name'] for l in database.get_leagues()])
if league_name is not None:

    if len(database.get_drafted_players(league_name)) < len(database.get_draft_order(league_name)):

        league = json.loads(database.get(f'league:{league_name}'))
        teams = database.get_teams(league_name)

        draft_order = database.get_draft_order(league_name)
        drafting_team = draft_order[len(database.get_drafted_players(league_name))]

        st.subheader(f"Drafting: {drafting_team['Owner']}")

        columns = st.columns([.5, .5])
        with columns[0]:

            st.subheader('My Team')
            my_players = database.get_drafted_players(league_name, drafting_team['Owner'])
            style = my_players.style.hide(axis=0)
            st.write(style.to_html(), unsafe_allow_html=True)

        with columns[1]:

            st.subheader('Available Players')
            undrafted_players = database.get_undrafted_players(league_name)
            undrafted_players.insert(0, 'Draft', False)
            event = st.data_editor(
                data=undrafted_players,
                hide_index=True,
                column_config={
                    "Draft": st.column_config.CheckboxColumn(
                        "Draft",
                        help="Select a player to draft them",
                        default=False,
                    )
                }
            )
            if event['Draft'].any():
                pdga_number = str(event[event['Draft'] == True].iloc[0]['PDGA #'])
                drafting_team['Players'].append(pdga_number)
                database.set(f"team:{league_name}:{drafting_team['Owner']}", json.dumps(drafting_team))
                st.rerun()

    else:

        st.text('Draft completed')