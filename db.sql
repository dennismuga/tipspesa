
-- Table structure for table subscribers
CREATE TABLE IF NOT EXISTS subscribers (
  id TEXT PRIMARY KEY,
  phone VARCHAR(20),
  password TEXT,
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

