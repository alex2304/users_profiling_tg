
/* Table 1 */
CREATE TABLE users (
  local_id SERIAL,
  tg_id INTEGER UNIQUE,
  first_name VARCHAR(250),
  last_name VARCHAR(250),
  username VARCHAR(250),

  PRIMARY KEY (local_id)
);

/* Table 2 */
CREATE TABLE chats (
  chat_id INTEGER,
  title VARCHAR(100),
  members_count INTEGER,
  messages_count INTEGER,
  creation_date TIMESTAMP,

  PRIMARY KEY (chat_id)
);

/* Table 3 */
CREATE TABLE users_in_chats (
  chat_id INTEGER,
  user_id INTEGER,
  entering_diff FLOAT,          -- difference between chat entering and chat creation (in seconds)
  avg_msg_frequency FLOAT,      -- average message frequency (messages/day) (for any types of messages)
  avg_msg_length FLOAT,         -- average messages length (only for text messages)

  PRIMARY KEY (chat_id, user_id),
  FOREIGN KEY (chat_id) REFERENCES chats (chat_id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users (local_id) ON DELETE CASCADE ON UPDATE CASCADE
);

/* Table 4 */
CREATE TABLE bots (
  title VARCHAR(50) UNIQUE,
  members_count INTEGER,

  PRIMARY KEY (title)
);

/* Table 5 */
CREATE TABLE users_in_bots (
  bot_title VARCHAR(50),
  user_id INTEGER,
  lang VARCHAR(10),

  PRIMARY KEY (bot_title, user_id),
  FOREIGN KEY (bot_title) REFERENCES bots (title) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users (local_id) ON DELETE CASCADE ON UPDATE CASCADE

);

/* Table 6 */
-- check message length
CREATE TABLE messages (
  msg_id INTEGER,
  text VARCHAR(500) NOT NULL,         -- only text messages shorter than 500 symbols
  date TIMESTAMP,
  chat_id INTEGER,
  user_id INTEGER,

  PRIMARY KEY (msg_id, user_id, chat_id),
  FOREIGN KEY (chat_id) REFERENCES chats (chat_id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users (local_id) ON DELETE CASCADE ON UPDATE CASCADE
);

/* Table 7 */
CREATE TABLE buses_clicks (
  click_id SERIAL,
  user_id INTEGER,

  click_timestamp TIMESTAMP,
  route_id VARCHAR(50),
  route_start_time TIMESTAMP,
  shuttle_id INTEGER,

  PRIMARY KEY (click_id),
  FOREIGN KEY (user_id) REFERENCES users (local_id) ON DELETE CASCADE ON UPDATE CASCADE
);

/* Table 8 */
CREATE TABLE food_orders (
  order_id SERIAL,
  user_id INTEGER,

  food_category VARCHAR(100),   -- determines from what bot it was ordered
  food_item VARCHAR(500),
  quantity INTEGER,
  order_timestamp TIMESTAMP,

  PRIMARY KEY (order_id),
  FOREIGN KEY (user_id) REFERENCES users (local_id) ON DELETE CASCADE ON UPDATE CASCADE
);

/* Table 9 */
CREATE TABLE placed_ads (
  ad_id SERIAL,
  user_id INTEGER,

  placed_timestamp TIMESTAMP,
  category_title VARCHAR(15),   -- rent / lostfound / ...
  ad_type VARCHAR(15),          -- sell / buy
  views_count INTEGER,
  likes_count INTEGER,

  PRIMARY KEY (ad_id),
  FOREIGN KEY (user_id) REFERENCES users (local_id) ON DELETE CASCADE ON UPDATE CASCADE
);
