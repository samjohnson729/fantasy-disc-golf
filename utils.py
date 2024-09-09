from datetime import datetime
from database import Database

database = Database()

def lock_in_teams():
    for league in database.list_leagues():
        for team in database.list_teams(league['league-name']):
            for event_id, event in database.EVENTS.items():
            
                # if event has already taken place or started
                if datetime.now() > datetime.strptime(event['start-date'], '%m-%d-%Y'):

                    # if the roster hasn't already been saved for this event
                    if event_id not in team['events']:
                        team['events'][event_id] = {
                            'players': team['players'],
                            'bench': team['bench']
                        }
                        database.save_team(league['league-name'], team)