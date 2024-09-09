import json, random
from io import StringIO
from datetime import datetime

import requests
import streamlit as st
import pandas as pd
import numpy as np
from redis import Redis

class Database(Redis):

    def __init__(self):
        super().__init__(**st.secrets['redis'])

        with open('./data/events.json') as f:
            self.EVENTS = json.load(f)

    @st.cache_data
    def get_players(_self, num_players:int=100):
        players = pd.DataFrame()
        page = 0
        while len(players) < num_players:
            response = requests.get(f'https://www.pdga.com/players/stats?page={page}&order=player_Rating&sort=desc')
            df = pd.read_html(StringIO(response.text))[0]
            players = pd.concat([players, df], ignore_index=True)
            players.drop_duplicates('PDGA #', keep='first', inplace=True)
            page += 1

        players = players[['Name', 'PDGA #', 'Rating', 'Events', 'Points', 'Cash']].copy()
        return players.iloc[:num_players].copy()

    def get_drafted_players(self, league_name:str, team_key:str='*'):
        drafted_players_ids = []
        for key in self.scan_iter(f'team:{league_name}:{team_key}'):
            team = json.loads(self.get(key))
            drafted_players_ids += team['players']

        all_players = self.get_players()
        drafted_players = all_players[all_players['PDGA #'].apply(lambda x: str(x) in drafted_players_ids)].copy()
        return drafted_players

    def get_undrafted_players(self, league_name:str, num_players:int=100):
        all_players = self.get_players()
        drafted_players = self.get_drafted_players(league_name)
        undrafted_players = all_players[all_players['PDGA #'].apply(lambda x: str(x) not in drafted_players['PDGA #'].astype(str).values)].copy()
        return undrafted_players

    def list_leagues(self):
        leagues = []
        for league_key in self.scan_iter(f'league:*'):
            league = self.get_json(league_key)
            if st.session_state.username in league['usernames']:
                leagues.append(league)
        return leagues
    
    def get_league(self, league_name:str):
        if league_name is not None:
            return self.get_json(f'league:{league_name}')
    
    def save_league(self, league:dict):
        key = f"league:{league['league-name']}"
        self.set(key, json.dumps(league))

    def delete_league(self, league_name:str):
        self.delete(f'league:{league_name}')
        for key in self.scan_iter(f'team:{league_name}:*'):
            self.delete(key)

    def list_teams(self, league_name:str):
        teams = []
        for team_key in self.scan_iter(f'team:{league_name}:*'):
            teams.append(self.get_json(team_key))
        return teams

    def get_team(self, league_name:str, username:str):
        return self.get_json(f'team:{league_name}:{username}')

    def save_team(self, league_name:str, team:dict):
        key = f"team:{league_name}:{team['username']}"
        self.set(key, json.dumps(team))

    def delete_team(self, league_name:str, username:str):
        self.delete(f'team:{league_name}:{username}')

    def get_drafting_team(self, league_name:str):
        league = self.get_league(league_name)
        teams = self.list_teams(league_name)
        random.seed(729)
        random.shuffle(teams)

        reverse = False
        draft_order = []
        for _ in range(league['roster-size']):
            if reverse: draft_order += list(reversed(teams))
            else: draft_order += teams
            reverse = not reverse

        num_picks = len(self.get_drafted_players(league_name))
        if num_picks < len(draft_order):
            return draft_order[num_picks]
    
    def get_matchups(self, league_name:str, event_id:int):

        def get_pairings(a):
            if len(a) == 2: return [[tuple(a)]]
            
            pairings = []
            for i in range(1, len(a)):
                pair = [(a[0], a[i])]
                remainder = [j for j in a if j not in [a[0], a[i]]]
                for sub_pairing in get_pairings(remainder):
                    pairings.append(pair + sub_pairing)
            return pairings
        
        # get initial matchups
        teams = self.list_teams(league_name)
        index = list(self.EVENTS).index(event_id)
        matchup_list, used_pairs = [], []
        for pairs in get_pairings(teams):
            for pair in pairs:
                if pair in used_pairs: break
            else:
                matchup_list.append(pairs)
                used_pairs += pairs

        # shuffle matchups and extend for full year
        random.seed(729)
        random.shuffle(matchup_list)
        while len(matchup_list) < len(self.EVENTS):
            matchup_list += matchup_list

        # return the current matchups
        return matchup_list[index]

    def get_current_event_id(self):
        for event_id, event in self.EVENTS.items():
            now = datetime.now()
            end_date = datetime.strptime(event['end-date'], '%m-%d-%Y')
            if (now - end_date).days < 2:
                return event_id

        st.warning('No upcoming or current events found')

    @st.cache_data(ttl=300)
    def get_event_results(_self, event_id:int, league_name:str):
        event_dict = requests.get(f'https://www.pdga.com/apps/tournament/live-api/live_results_fetch_event?TournID={event_id}').json()['data']

        results = {}
        for round in event_dict['RoundsList'].keys():
            pools = requests.get(f'https://www.pdga.com/apps/tournament/live-api/live_results_fetch_round?TournID={event_id}&Division=MPO&Round={round}').json()['data']
            pools = [pools] if isinstance(pools, dict) else pools
            for data in pools:
                pars = np.array([hole['Par'] for hole in data['holes']])
                for record in data['scores']:
                    try:
                        scores = np.array([int(score) for score in record['HoleScores'] if score != ''])
                        results[record['PDGANum']] = {
                            'Name':             record['Name'],
                            'Ace':              results.get(record['PDGANum'], {}).get('Ace', 0) + sum(scores == 1),
                            'Albatross':        results.get(record['PDGANum'], {}).get('Albatross', 0) + sum(scores - pars[:len(scores)] == -3),
                            'Eagle':            results.get(record['PDGANum'], {}).get('Eagle', 0) + sum(scores - pars[:len(scores)] == -2),
                            'Birdie':           results.get(record['PDGANum'], {}).get('Birdie', 0) + sum(scores - pars[:len(scores)] == -1),
                            'Par':              results.get(record['PDGANum'], {}).get('Par', 0) + sum(scores - pars[:len(scores)] == 0),
                            'Bogey':            results.get(record['PDGANum'], {}).get('Bogey', 0) + sum(scores - pars[:len(scores)] == 1),
                            'Double Bogey':     results.get(record['PDGANum'], {}).get('Double Bogey', 0) + sum(scores - pars[:len(scores)] == 2),
                            'Triple+ Bogey':    results.get(record['PDGANum'], {}).get('Triple+ Bogey', 0) + sum(scores - pars[:len(scores)] >= 3),
                            'Score':            record['ToPar'],
                            'Position':         int(record['RunningPlace'])
                        }
                    except:
                        pass

        results = pd.DataFrame.from_dict(results, orient='index')
        results.index = results.index.astype(str)
        results['Points'] = results.apply(lambda x: _self.calculate_score(league_name, x), axis=1)

        return results

    def calculate_score(self, league_name:str, row):
        league = json.loads(self.get(f'league:{league_name}'))
        hole_score_dict = league['scoring']['hole-score']
        tournament_position_dict = league['scoring']['tournament-position']

        output = sum([
            hole_score_dict['ace'] * row['Ace'],
            hole_score_dict['albatross'] * row['Albatross'],
            hole_score_dict['eagle'] * row['Eagle'],
            hole_score_dict['birdie'] * row['Birdie'],
            hole_score_dict['par'] * row['Par'],
            hole_score_dict['bogey'] * row['Bogey'],
            hole_score_dict['double bogey'] * row['Double Bogey'],
            hole_score_dict['triple+ bogey'] * row['Triple+ Bogey']
        ])

        for key, value in tournament_position_dict.items():
            if row['Position'] <= int(key):
                output += value
                break

        return output

    def get_json(self, key:str):
        return json.loads(self.get(key))
