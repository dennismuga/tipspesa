-- Table structure for table subscribers
CREATE TABLE IF NOT EXISTS matches (
	match_id TEXT PRIMARY KEY,
	kickoff TIMESTAMP,
	home_team TEXT,
	away_team TEXT,
	prediction TEXT,
	odd DOUBLE PRECISION,
	home_results INT,
	status TEXT,
	away_results INT,
	overall_prob DOUBLE PRECISION,
	sub_type_id INT,
	parent_match_id INT,
	bet_pick TEXT,
	outcome_id INT,
	special_bet_value TEXT
);

-- Table structure for table subscribers
CREATE TABLE IF NOT EXISTS subscribers (
  id TEXT PRIMARY KEY,
  phone TEXT,
  expires_at TIMESTAMP,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  UNIQUE (phone)
);

-- Table structure for table selections
CREATE TABLE IF NOT EXISTS jackpot_selections (
  id BIGINT,
  provider TEXT,
  event_id BIGINT,
  start_date TIMESTAMP,
  home TEXT,
  away TEXT,
  home_odds DOUBLE PRECISION,
  draw_odds DOUBLE PRECISION,
  away_odds DOUBLE PRECISION,
  prediction TEXT,
  created_at TIMESTAMP
);

-- Table structure for table safaricom_callback
CREATE TABLE IF NOT EXISTS safaricom_callback (
  id SERIAL PRIMARY KEY,
  response TEXT,
  status INT DEFAULT 0,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Table structure for transactions
CREATE TABLE IF NOT EXISTS transactions (
  id TEXT PRIMARY KEY,
  subscriber_id TEXT,
  amount INT DEFAULT 0,
  payment_method TEXT,
  payment_account TEXT,
  confirmation_code TEXT,
  status TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Table structure for odds
CREATE TABLE IF NOT EXISTS odds (
  id TEXT PRIMARY KEY,
  parent_match_id INT,
  sub_type_id INT,
  bet_pick TEXT,
  odd_value DOUBLE PRECISION,
  outcome_id INT,
  sport_id INT,
  special_bet_value TEXT,
  bet_type INT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Table structure for table profiles
CREATE TABLE IF NOT EXISTS profiles (
  phone TEXT PRIMARY KEY,
  password TEXT,
  profile_id INT
  is_active BOOLEAN DEFAULT 'TRUE'
);

-- Table structure for table betslips
CREATE TABLE IF NOT EXISTS betslips (
  id SERIAL PRIMARY KEY,
  code TEXT,
  parent_match_id INT,
  profile_id INT
);
