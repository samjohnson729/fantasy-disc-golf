import streamlit as st
import pandas as pd
from database import Database
from navigation import make_sidebar
import matchup
import utils

utils.lock_in_teams()
make_sidebar()
database = Database()

league_name = st.selectbox('League', [l['league-name'] for l in database.list_leagues()])
league = database.get_league(league_name)

if league is not None:

    tabs = st.tabs(['Match', 'Team', 'Players', 'League'])

    with tabs[0]:

    
        all_matchups = database.get_matchups(league_name, database.get_current_event_id())
        all_matchup_strings = [f"{m[0]['username']} vs {m[1]['username']}" for m in all_matchups]

        controls = st.columns(2)
        with controls[0]:
            event_names = [e['name'] for e in database.EVENTS.values()]
            current_event_idx = list(database.EVENTS.keys()).index(database.get_current_event_id())
            selected_event_name = st.selectbox('Event', event_names, current_event_idx)
            selected_event_i = list(database.EVENTS.keys())[event_names.index(selected_event_name)]
        with controls[1]:
            selected_matchup_string = st.selectbox('Matchup', all_matchup_strings)
            selected_matchup = all_matchups[all_matchup_strings.index(selected_matchup_string)]

        matchup.render(selected_event_i, league, selected_matchup)

    with tabs[1]:

        team = database.get_team(league_name, st.session_state.username)
        my_players = database.get_drafted_players(league_name, st.session_state.username)

        active_players = my_players[my_players['PDGA #'].apply(lambda x: str(x) not in team['bench'])].copy()
        bench_players = my_players[my_players['PDGA #'].apply(lambda x: str(x) in team['bench'])].copy()

        st.subheader('Active')
        active_players.insert(0, 'Bench', False)
        active_players.insert(0, 'Drop', False)
        event = st.data_editor(
            data=active_players,
            hide_index=True,
            disabled=my_players.columns
        )
        if event['Drop'].any():
            pdga_num = str(event[event['Drop']].iloc[0]['PDGA #'])
            team['players'].remove(pdga_num)
            database.save_team(league_name, team)
            st.rerun()
        if event['Bench'].any():
            pdga_num = str(event[event['Bench']].iloc[0]['PDGA #'])
            team['bench'].append(pdga_num)
            database.save_team(league_name, team)
            st.rerun()

        st.subheader('Bench')
        bench_players.insert(0, 'Activate', False)
        bench_players.insert(0, 'Drop', False)
        event = st.data_editor(
            data=bench_players,
            hide_index=True,
            disabled=my_players.columns
        )
        if event['Drop'].any():
            pdga_num = str(event[event['Drop']].iloc[0]['PDGA #'])
            team['players'].remove(pdga_num)
            team['bench'].remove(pdga_num)
            database.save_team(league_name, team)
            st.rerun()
        if event['Activate'].any():
            if len(active_players) < league['roster-size'] - league['bench-size']:
                pdga_num = str(event[event['Activate']].iloc[0]['PDGA #'])
                team['bench'].remove(pdga_num)
                database.save_team(league_name, team)
                st.rerun()
            else:
                st.error('You must move an active player to your bench first')

    with tabs[2]:

        my_team = database.get_team(league_name, st.session_state.username)
        undrafted_players = database.get_undrafted_players(league_name)
        disabled_columns = undrafted_players.columns
        undrafted_players.insert(0, 'Add', False)

        event = st.data_editor(
            data=undrafted_players,
            hide_index=True,
            disabled=disabled_columns,
        )
        if event['Add'].any():
            pdga_num = str(event[event['Add']].iloc[0]['PDGA #'])
            if len(my_team['players']) < league['roster-size']:
                active_players = len(my_team['players']) - len(my_team['bench'])
                active_players_allowed = league['roster-size'] - league['bench-size']
                my_team['players'].append(pdga_num)
                if active_players >= active_players_allowed:
                    my_team['bench'].append(pdga_num)
                database.save_team(league_name, my_team)
                st.rerun()
            else:
                st.error('You must drop a player before you can add a new player')

    with tabs[3]:
        #st.header('League')
        pass
