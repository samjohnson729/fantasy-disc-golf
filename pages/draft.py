import json

import streamlit as st
import pandas as pd

from database import Database
from navigation import make_sidebar

make_sidebar()

database = Database()

@st.fragment(run_every=5)
def render_draft_board(league_name:str):
    drafting_team = database.get_drafting_team(league_name)
    if drafting_team is not None:

        st.subheader(f"Drafting: {drafting_team['username']}")

        teams = database.list_teams(league_name)
        tabs = st.tabs([t['username'] for t in teams])
        for i, team in enumerate(teams):
            with tabs[i]:
                my_players = database.get_drafted_players(league_name, team['username'])
                style = my_players.style.hide(axis=0)
                st.write(style.to_html(), unsafe_allow_html=True)

        undrafted_players = database.get_undrafted_players(league_name)
        disabled_columns = undrafted_players.columns.tolist()
        if drafting_team['username'] != st.session_state.username:
            disabled_columns += ['Draft']
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
            },
            disabled=disabled_columns,
        )
        if event['Draft'].any():
            pdga_number = str(event[event['Draft'] == True].iloc[0]['PDGA #'])
            drafting_team['players'].append(pdga_number)
            if len(drafting_team['players']) > league['roster-size'] - league['bench-size']:
                drafting_team['bench'].append(pdga_number)
            database.save_team(league_name, drafting_team)
            database.set(f"team:{league_name}:{drafting_team['username']}", json.dumps(drafting_team))
            st.rerun()

    else:
        league['draft-status'] = 'after'
        database.set(f'league:{league_name}', json.dumps(league))
        st.switch_page('pages/home.py')

st.title('Draft')

league_name = st.selectbox('League', [l['league-name'] for l in database.list_leagues()])
league = database.get_league(league_name)

if league is not None:
    render_draft_board(league_name)