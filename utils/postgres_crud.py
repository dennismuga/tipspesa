import os, uuid, psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

from utils.entities import Event, Jackpot, Odds, User

class PostgresCRUD:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        self.conn_params = {
            'host': os.getenv('DB_HOST'),
            'database': os.getenv('DB_NAME'),
            'port': os.getenv('DB_PORT'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        self.conn = None
        self.ensure_connection()
    
    def ensure_connection(self):
        try:
            # Check if the connection is open
            if self.conn is None or self.conn.closed:
                self.conn = psycopg2.connect(**self.conn_params)
            else:
                # Test the connection
                with self.conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
        except Exception as e:
            # Reconnect if the connection is invalid
            self.conn = psycopg2.connect(**self.conn_params)
          
    def insert_match_old(self, match):
        kickoff = match['start_time']
        home_team = match['home_team'].replace("'","''")
        away_team = match['away_team'].replace("'","''")
        prediction = match['prediction']
        match_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f'{kickoff.date()}{home_team}{away_team}'))
        odd = match['odd']
        match_url = match['match_url'].replace("#","*")
        meetings = match['meetings']
        average_goals_home = match['average_goals_home']
        average_goals_away = match['average_goals_away']
        overall_prob = match['overall_prob']
        over_0_5_home_perc = match['over_0_5_home_perc']
        over_0_5_away_perc = match['over_0_5_away_perc']
        over_1_5_home_perc = match['over_1_5_home_perc']
        over_1_5_away_perc = match['over_1_5_away_perc']
        over_2_5_home_perc = match['over_2_5_home_perc']
        over_2_5_away_perc = match['over_2_5_away_perc']
        over_3_5_home_perc = match['over_3_5_home_perc']
        over_3_5_away_perc = match['over_3_5_away_perc']
        analysis = match['analysis']        
        
        analysis = match['analysis'].replace("'","''")
        
        self.ensure_connection()
        with self.conn.cursor() as cursor:
            query = """
                INSERT INTO matches(match_id, kickoff, home_team, away_team, prediction, odd, match_url, meetings, average_goals_home, average_goals_away, overall_prob,
                over_0_5_home_perc, over_0_5_away_perc, over_1_5_home_perc, over_1_5_away_perc, over_2_5_home_perc, over_2_5_away_perc, over_3_5_home_perc, over_3_5_away_perc, analysis)
                VALUES(%s, %s + INTERVAL '2 hours', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (match_id) DO UPDATE SET
                    prediction = %s,
                    overall_prob = %s,
                    analysis = %s
            """
            cursor.execute(query, (match_id, kickoff, home_team, away_team, prediction, odd, match_url , meetings, average_goals_home, average_goals_away, overall_prob, 
                                   over_0_5_home_perc, over_0_5_away_perc, over_1_5_home_perc, over_1_5_away_perc, over_2_5_home_perc, over_2_5_away_perc, over_3_5_home_perc,
                                   over_3_5_away_perc, analysis, prediction, overall_prob, analysis))
            self.conn.commit()
    
    def insert_matches(self, matches):                
        self.ensure_connection()
        with self.conn.cursor() as cursor:
            query = """
                INSERT INTO matches(match_id, kickoff, home_team, away_team, prediction, odd, overall_prob, parent_match_id, sub_type_id, bet_pick, special_bet_value, outcome_id)
                VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (match_id) DO UPDATE SET
                    prediction = %s,
                    odd = %s,
                    overall_prob = %s     
                """
                
            values = [
                (
                    str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{match['match_id']}{match['prediction']}")),
                    match['start_time'],
                    match['home_team'].replace("'","''"),
                    match['away_team'].replace("'","''"),
                    match['prediction'],
                    match['odd'],
                    match['overall_prob'],
                    match['parent_match_id'],
                    match['sub_type_id'],
                    match['bet_pick'],
                    match['special_bet_value'],
                    match['outcome_id'],
                    match['prediction'],
                    match['odd'],
                    match['overall_prob']
                ) for match in matches
            ]
            cursor.executemany(query, values)
            self.conn.commit()
            
    def fetch_open_matches(self):
        self.ensure_connection()
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT *
                FROM matches
                WHERE (status IS NULL OR status = 'LIVE')
                    AND DATE(kickoff) >= CURRENT_DATE
                ORDER BY kickoff DESC
            """
            cur.execute(query)
            return cur.fetchall()
            
    def get_predictions(self):
        self.ensure_connection()
        with self.conn.cursor() as cur:
            query = """
                WITH filtered AS(
                    SELECT parent_match_id, prediction, odd, overall_prob, special_bet_value, outcome_id, sub_type_id, kickoff,
                        ROW_NUMBER() OVER (PARTITION BY parent_match_id ORDER BY odd DESC) AS rn
                    FROM matches
                    WHERE DATE(kickoff) >= CURRENT_DATE
                )
                SELECT * FROM filtered
                WHERE rn = 1
                ORDER BY kickoff
            """
            cur.execute(query)
            
            predictions = []
            for datum in cur.fetchall():
                prediction = {
                    'parent_match_id': datum[0],
                    'bet_pick': 'GG' if datum[1] == 'GG' else datum[1],
                    'odd_value': datum[2],
                    'overall_prob': datum[3],
                    'special_bet_value': datum[4],
                    'outcome_id': datum[5],
                    'sub_type_id': datum[6]
                }
                predictions.append(prediction)
        return predictions
    
    def fetch_matches(self, day, comparator, status, limit=16): 
        self.ensure_connection()           
        with self.conn.cursor() as cur:
            query = f"""
            WITH m AS(
                SELECT matches.* 
                FROM matches
                INNER JOIN source_model ON source_model.parent_match_id=matches.parent_match_id
                WHERE matches.kickoff::date {comparator} (CURRENT_TIMESTAMP + INTERVAL '3 hours')::date {day} {status}
                AND model IN ('xai/grok-3')
                --AND (status != 'LOST' OR status IS NULL)
                --AND overall_prob >= 70 
                --AND sub_type_id NOT IN (1)
                --AND outcome_id NOT IN (11)
                --AND bet_pick NOT IN ('over 1.5', 'under 3.5', 'under 4.5', 'yes')
                ORDER BY odd DESC, overall_prob DESC
                LIMIT {limit}
            )
            SELECT * 
            FROM m
            ORDER BY kickoff, overall_prob DESC, odd DESC, match_id
            """
            cur.execute(query)
            return cur.fetchall()
    
    def fetch_unplaced_matches(self, profile_id, limit=50): 
        self.ensure_connection()  
        matches = []         
        with self.conn.cursor() as cur:
            query = f"""
            WITH m AS(
                SELECT kickoff, home_team, away_team, odd, parent_match_id, sub_type_id, bet_pick, special_bet_value, outcome_id 
                FROM matches
                WHERE kickoff > (CURRENT_TIMESTAMP + INTERVAL '3 hours')
                AND overall_prob >= 80
                AND sub_type_id NOT IN (1)
                AND outcome_id NOT IN (11)
                AND outcome_id IN (9,10)
                AND bet_pick NOT IN ('over 1.5', 'under 4.5')
                ORDER BY odd DESC, overall_prob DESC
                LIMIT {limit}
            ),
            placed AS(
              SELECT parent_match_id 
              FROM betslips 
              WHERE profile_id = %s
            )
            SELECT * 
            FROM m
            WHERE parent_match_id NOT IN(
              SELECT parent_match_id FROM placed
            )
            ORDER BY kickoff
            """
            cur.execute(query, (profile_id,)) 
            for datum in cur.fetchall():
                match = {
                    'start_time': datum[0],
                    'home_team': datum[1],
                    'away_team': datum[2],
                    'odd': datum[3],
                    'parent_match_id': datum[4],
                    'sub_type_id': datum[5],
                    'bet_pick': datum[6],
                    'special_bet_value': datum[7],
                    'outcome_id': datum[8]
                }
                matches.append(match)
        return matches
    
    def add_bet_slip(self, profile_id, slips, code):
        """
        Add multiple bet slips for a profile.
        Each slip should be a dict with a 'parent_match_id' key.
        """
        self.ensure_connection()
        try:
            with self.conn.cursor() as cur:
                query = """
                    INSERT INTO betslips(code, profile_id, parent_match_id)
                    VALUES(%s, %s, %s)
                """
                values = [
                    (code, profile_id, slip['parent_match_id']) for slip in slips
                ]
                cur.executemany(query, values)
                self.conn.commit()
        except Exception as e:
            print(f"Error adding bet slips: {e}")
    
    def update_match_results(self, match_id, home_results, away_results, status):        
        self.ensure_connection()
        with self.conn.cursor() as cur:
            query = """
                UPDATE matches SET
                    home_results = %s,
                    away_results = %s,
                    status = %s
                WHERE match_id = %s
            """
            
            cur.execute(query, (home_results, away_results, status, match_id)) 
            self.conn.commit()    
        
    def fetch_subscribers(self, status, sms=None):
        self.ensure_connection()
        with self.conn.cursor() as cur:
            query = """
                SELECT phone
                FROM subscribers
                WHERE status = %s AND (last_delivered_at IS NULL OR DATE(last_delivered_at) < current_date)
            """
            if sms is None:
                # If sms is None, find subscribers whose phone contains "@"
                query += " AND phone LIKE %s"
                phone_filter = '%@%'  # Look for phones containing '@'
            else:
                # If sms, find subscribers whose phone does not contain "@"
                query += " AND phone NOT LIKE %s"
                phone_filter = '%@%'  # Look for phones that do not contain '@'
            
            # Execute the query with both status and phone_filter
            cur.execute(query, (status, phone_filter))
        
            return cur.fetchall()
    
    def add_or_remove_subscriber(self, phone, status=1):         
        self.ensure_connection()
        with self.conn.cursor() as cur:
            query = """
                INSERT INTO subscribers(phone, status, created_at)
                VALUES(%s, %s, NOW())
                ON CONFLICT (phone) DO UPDATE SET
                    status = %s,
                    last_delivered_at = NULL,
                    updated_at = NOW()
            """
            
            cur.execute(query, (phone, status, status)) 
            self.conn.commit()         
    
    def update_subscriber_on_send(self, phone):         
        self.ensure_connection()
        with self.conn.cursor() as cur:
            query = """
                UPDATE subscribers
                SET last_delivered_at=NOW()
                WHERE phone = %s
            """
            
            cur.execute(query, (phone,)) 
            self.conn.commit()         
    
    def update_subscriber_on_dlr(self, phone):         
        self.ensure_connection()
        with self.conn.cursor() as cur:
            query = """
                UPDATE subscribers
                SET last_delivered_at=NOW()
                WHERE phone = %s
            """
            
            cur.execute(query, (phone, )) 
            self.conn.commit()
                
    def add_jackpot_selections(self, jackpots):         
        self.ensure_connection()
        with self.conn.cursor() as cur:
            query = """
                INSERT INTO jackpot_selections(id, provider, event_id, start_date, home, away, home_odds, draw_odds, away_odds, created_at)
                VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """
            
            for jackpot in jackpots:
                for event in jackpot.events:
                    for odds in event.odds:
                        cur.execute(query, (jackpot.id, jackpot.provider, event.id, event.start_date, event.home, event.away, odds.home_odds, odds.draw_odds, odds.away_odds)) 
                
            self.conn.commit()
            self.conn.close()
    
        
    def fetch_jackpots(self):
        self.ensure_connection()
        selections = []
        with self.conn.cursor() as cur:
            query = """
                SELECT DISTINCT id, provider
                FROM jackpot_selections
            """
            cur.execute(query)
            data = cur.fetchall()
            for datum in data:
                events = self.fetch_events(datum[0])
                selections.append(Jackpot(datum[0], datum[1], events))
                  
        return selections
      
    def fetch_events(self, jackpot_id):
        self.ensure_connection()
        events = []
        with self.conn.cursor() as cur:
            query = """
                WITH latest_selections AS (
                    SELECT event_id, start_date, home, away, prediction, created_at,
                        ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY created_at DESC) AS rn
                    FROM jackpot_selections
                    WHERE id = %s AND start_date > NOW()
                )
                SELECT event_id, start_date, home, away, prediction, created_at
                FROM latest_selections
                WHERE rn = 1
                ORDER BY created_at DESC
            """
            cur.execute(query,(jackpot_id, ))
            data = cur.fetchall()
            for datum in data:
                odds = self.fetch_odds(datum[0])
                events.append(Event(datum[0], datum[1], datum[2], datum[3], odds, datum[4]))
                  
        return events
    
    def fetch_odds(self, event_id):
        self.ensure_connection()
        selection_odds = []
        with self.conn.cursor() as cur:
            query = """
                SELECT home_odds, draw_odds, away_odds, created_at
                FROM jackpot_selections
                WHERE event_id = %s
                ORDER BY created_at
            """
            cur.execute(query,(event_id,))
            data = cur.fetchall()
            for datum in data:
                selection_odds.append(Odds(datum[0], datum[1], datum[2], datum[3]))
            
        return selection_odds
    
    # def fetch_all_odds(self):
    #     self.ensure_connection()
    #     query = """
    #         SELECT id, event_id, home_odds, draw_odds, away_odds, created_at
    #         FROM jackpot_selections
    #         ORDER BY created_at
    #     """
            
    #     return pd.read_sql_query(query, self.conn)
                
    def update_prediction_to_jackpot_selections(self, odds_df):         
        self.ensure_connection()
        with self.conn.cursor() as cur:
            for index, row in odds_df.iterrows():
                query = """
                UPDATE jackpot_selections
                SET prediction = %s
                WHERE id=%s AND event_id = %s AND prediction IS NULL
                """
                cur.execute(query, (row['prediction'], row['id'], row['event_id']))
                
            self.conn.commit()
            self.conn.close()
                
    def save_safaricom_callback(self, response):         
        self.ensure_connection()
        with self.conn.cursor() as cur:
            query = """
            INSERT INTO safaricom_callback(response, created_at)
            VALUES(%s, NOW())
            """
            cur.execute(query, (response,))
                
            self.conn.commit()
            self.conn.close()

    def insert_sms(self, payload):
        id = str(uuid.uuid5(uuid.NAMESPACE_DNS, payload))        
        self.ensure_connection()
        with self.conn.cursor() as cursor:
            query = """
                INSERT INTO sms(id, payload)
                VALUES(%s, %s)
                ON CONFLICT DO NOTHING
            """
            cursor.execute(query, (id, payload))
            self.conn.commit()
    
    def verify_code(self, code):
        self.ensure_connection()
        with self.conn.cursor() as cur:
            query = """
                SELECT *
                FROM sms
                WHERE payload LIKE %s
            """
            cur.execute(query,(f'%{code}%',))
            data = cur.fetchone()
            if data:
                return code
            
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, code)).split('-')
    
    def add_user(self, phone):
        id = str(uuid.uuid5(uuid.NAMESPACE_DNS, phone))        
        self.ensure_connection()
        with self.conn.cursor() as cursor:
            query = """
                INSERT INTO subscribers(id, phone, expires_at)
                VALUES(%s, %s, NOW())
                ON CONFLICT DO NOTHING
            """
            cursor.execute(query, (id, phone))
            self.conn.commit()      
    
    def update_user_expiry(self, order_tracking_id, plan, days=1):         
        self.ensure_connection()
        with self.conn.cursor() as cur:
            query = """
                UPDATE subscribers
                SET password=%s, expires_at = NOW() + INTERVAL '%s days' 
                WHERE id = (SELECT subscriber_id FROM transactions WHERE id = %s)
            """

            cur.execute(query, (plan, days, order_tracking_id)) 
            self.conn.commit()  

    def get_user(self, user_id=None, phone=None):
        self.ensure_connection()
        with self.conn.cursor() as cur:
            query = """
                SELECT id, phone, password, DATE(expires_at) > CURRENT_DATE AS active
                FROM subscribers
                WHERE 1=1
            """
            params = []
            if user_id:
                query = f'{query} AND id = %s'
                params.append(user_id)
            if phone:
                query = f'{query} AND phone = %s'
                params.append(phone)
            cur.execute(query, tuple(params))            
            datum = cur.fetchone()
            if datum:
                return User(datum[0], datum[1], datum[2], datum[3])
            else:
                return None
    
    def insert_transaction(self, id, subscriber_id, amount):
        self.ensure_connection()
        with self.conn.cursor() as cursor:
            query = """
                INSERT INTO transactions(id, subscriber_id, amount, created_at)
                VALUES(%s, %s, %s, NOW())
                ON CONFLICT DO NOTHING
            """
            cursor.execute(query, (id, subscriber_id, amount))
            self.conn.commit()   
    
    def update_transaction(self, id, payment_method, payment_account, confirmation_code, status):
        self.ensure_connection()
        with self.conn.cursor() as cursor:
            query = """
                UPDATE transactions
                SET payment_method=%s, payment_account=%s, confirmation_code=%s, status=%s, updated_at=NOW()
                WHERE id=%s
            """
            cursor.execute(query, (payment_method, payment_account, confirmation_code, status, id))
            self.conn.commit()    
    
    def insert_odds(self, id, parent_match_id, sub_type_id, bet_pick, odd_value, outcome_id, sport_id, special_bet_value, bet_type):
        self.ensure_connection()
        try:
            with self.conn.cursor() as cursor:
                query = """
                    INSERT INTO odds(id, parent_match_id, sub_type_id, bet_pick, odd_value, outcome_id, sport_id, special_bet_value, bet_type, created_at)
                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT DO NOTHING
                """
                cursor.execute(query, (id, parent_match_id, sub_type_id, bet_pick, odd_value, str(outcome_id), sport_id, special_bet_value, bet_type))
                self.conn.commit()    
        except Exception as e:
            print(f"Error inserting odds: {e}") 
               
    def delete_inactive_odds(self, parent_match_id, sub_type_id):
        self.ensure_connection()
        try:
            with self.conn.cursor() as cursor:
                query = """
                    DELETE FROM odds
                    WHERE parent_match_id = %s AND sub_type_id = %s
                """
                cursor.execute(query, (parent_match_id, sub_type_id))
                self.conn.commit()
        except Exception as e:
            print(f"Error deleting odds: {e}")
    
    def delete_expired_odds(self, parent_match_ids):
        self.ensure_connection()
        try:
            with self.conn.cursor() as cursor:
                query = """
                    DELETE FROM odds
                    WHERE parent_match_id NOT IN %s
                """
                cursor.execute(query, (tuple(parent_match_ids),))
                self.conn.commit()
        except Exception as e:
            print(f"Error deleting odds: {e}")

    def get_odds_history(self, match_id, market, limit=10):
        self.ensure_connection()
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT odd_value FROM odds 
                    WHERE parent_match_id = %s AND bet_pick = %s 
                    ORDER BY updated_at DESC LIMIT %s
                """
                cursor.execute(query, (match_id, market, limit))
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching odds history: {e}")
            return []

    def get_active_odds(self):
        self.ensure_connection()
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT id, parent_match_id, sub_type_id, bet_pick, odd_value, outcome_id, sport_id, special_bet_value, bet_type
                    FROM odds
                """
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching active odds: {e}")
            return []
    
    def get_active_profiles(self):
        self.ensure_connection()
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT phone, password, profile_id
                    FROM profiles
                    WHERE is_active IS TRUE
                """
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching active profiles: {e}")
            return []

    
                  
# Example usage:
if __name__ == "__main__":
    crud = PostgresCRUD()







