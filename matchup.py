import streamlit as st
import pandas as pd
from database import Database

database = Database()

def render(event_id:int, league:dict, matchup:tuple):

    event = database.EVENTS.get(event_id)
    left_team, right_team = matchup
    results = database.get_event_results(event_id, league['league-name'])

    # add in 0 stats for DNP players
    for player in database.get_drafted_players(league['league-name']).to_dict('records'):
        if str(player['PDGA #']) not in results.index:
            results.loc[str(player['PDGA #'])] = pd.Series({'Name': player['Name'], 'Position': 'N/A'})
    results.fillna(0, inplace=True)
    results = results.map(lambda x: int(x) if isinstance(x, float) else x)

    st.subheader(event['name'])

    left_players = results.loc[results.index.intersection(left_team['players'])].sort_values('Points', ascending=False).copy()
    left_bench = results.loc[results.index.intersection(left_team['bench'])].sort_values('Points', ascending=False).copy()
    left_starters = left_players.drop(left_bench.index)

    right_players = results.loc[results.index.intersection(right_team['players'])].sort_values('Points', ascending=False).copy()
    right_bench = results.loc[results.index.intersection(right_team['bench'])].sort_values('Points', ascending=False).copy()
    right_starters = right_players.drop(right_bench.index)

    st.write('Total')
    columns = st.columns(2, gap='small', vertical_alignment='top')
    with columns[0]:
        left_total = left_starters.sum(0, numeric_only=True)
        left_total['Name'] = left_team['username']
        left_total['Position'] = 'N/A'
        render_player(league, left_total)
    with columns[1]:
        right_total = right_starters.sum(0, numeric_only=True)
        right_total['Name'] = right_team['username']
        right_total['Position'] = 'N/A'
        render_player(league, right_total)

    st.divider()
    st.write('Starters')

    for i in range(max(len(left_starters), len(right_starters))):
        columns = st.columns(2, gap='medium')
        with columns[0]:
            if len(left_starters) > i:
                render_player(league, left_starters.iloc[i])
        with columns[1]:
            if len(right_starters) > i:
                render_player(league, right_starters.iloc[i])

    st.divider()
    st.write('Bench')

    for i in range(max(len(left_bench), len(right_bench))):
        columns = st.columns(2, gap='medium')
        with columns[0]:
            if len(left_bench) > i:
                render_player(league, left_bench.iloc[i])
        with columns[1]:
            if len(right_bench) > i:
                render_player(league, right_bench.iloc[i])

def render_player(league:dict, player:pd.Series):
    with st.container(border=True):
        controls = st.columns([.75,.25], vertical_alignment='center')
        with controls[0]:
            st.write(player['Name'])
            score_string = []

            # get scores for individual holes
            for score in ['Ace', 'Albatross', 'Eagle', 'Birdie', 'Par', 'Bogey', 'Double Bogey', 'Triple+ Bogey']:
                if player.get(score, 0) != 0:
                    score_string.append(f"{score}: {player[score]} ({player[score] * league['scoring']['hole-score'][score.lower()]})")
            
            # get score from tournament position
            position = player.get('Position')
            if isinstance(position, int):
                position_score = 0
                for key, value in league['scoring']['tournament-position'].items():
                    if position <= int(key):
                        position_score = value
                        break
                score_string.append(f"Position: {position} ({position_score})")

            st.text('\n'.join(score_string))
        with controls[1]:
            st.metric('points', int(player['Points']), label_visibility='hidden')
