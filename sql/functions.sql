-- use SQL statement instead of functions for inserting chats and bots (there are no such functions here)

-- update or insert user
CREATE OR REPLACE FUNCTION insert_user(user_id INTEGER, first_name VARCHAR(250), last_name VARCHAR(250), username VARCHAR(250)) RETURNS VOID AS $$
  BEGIN

    -- if the user exists - update it, otherwise - add new user
    IF user_id IN (SELECT tg_id FROM users) THEN
      UPDATE users SET (first_name, last_name, username) = ($2, $3, $4)
      WHERE users.tg_id = user_id;
    ELSE
      INSERT INTO users (tg_id, first_name, last_name, username) VALUES ($1, $2, $3, $4);
    END IF;

  END;
$$ LANGUAGE plpgsql;

-- replace user_id with the local id
CREATE OR REPLACE FUNCTION insert_user_in_chat(_chat_id INTEGER, _user_id INTEGER, _entering_diff FLOAT, _avg_msg_frequency FLOAT, _avg_msg_length FLOAT) RETURNS VOID AS $$
  DECLARE
    local_user_id INTEGER := (SELECT local_id FROM users WHERE tg_id = _user_id);
  BEGIN

    -- check if the chat exists
    IF _chat_id NOT IN (SELECT chat_id FROM chats) THEN
      RAISE EXCEPTION 'Error inserting user in chat: there is no chat with the given chat_id';
    END IF;

    -- if there is no such user - insert it into the Users table
    IF _user_id NOT IN (SELECT tg_id FROM users) THEN
      INSERT INTO users (tg_id, first_name, last_name, username) VALUES (_user_id, NULL, NULL, NULL);
      local_user_id := (SELECT local_id FROM users WHERE tg_id = user_id);
    END IF;

    -- if the user_in_chat exists - update it; otherwise - add new one
    IF (_chat_id, local_user_id) IN (SELECT chat_id, user_id FROM users_in_chats) THEN
      UPDATE users_in_chats SET (entering_diff, avg_msg_frequency, avg_msg_length) = (_entering_diff, _avg_msg_frequency, _avg_msg_length)
      WHERE chat_id = _chat_id AND user_id = local_user_id;
    ELSE
      INSERT INTO users_in_chats VALUES (_chat_id, local_user_id, _entering_diff, _avg_msg_frequency, _avg_msg_length);
    END IF;

  END;
$$ LANGUAGE plpgsql;

SELECT * FROM insert_user_in_bot('InnoHelpBot', 216842240, 'en');
-- replace user_id with the local id
CREATE OR REPLACE FUNCTION insert_user_in_bot(_bot_title VARCHAR(50), _user_id INTEGER, _lang VARCHAR(10)) RETURNS VOID AS $$
  DECLARE
    local_user_id INTEGER := (SELECT local_id FROM users WHERE tg_id = _user_id);
  BEGIN

    -- check if the bot exists
    IF _bot_title NOT IN (SELECT title FROM bots) THEN
      RAISE EXCEPTION 'Error inserting user in bot: there is no bot with the given bot title';
    END IF;

    -- if there is no such user - add it into the Users table
    IF _user_id NOT IN (SELECT tg_id FROM users) THEN
      INSERT INTO users (tg_id, first_name, last_name, username) VALUES (_user_id, NULL, NULL, NULL);
      local_user_id := (SELECT local_id FROM users WHERE tg_id = _user_id);
    END IF;

    -- if the user_in_bot exists - update it; otherwise - add new one
    IF (_bot_title, local_user_id) IN (SELECT bot_title, user_id FROM users_in_bots) THEN
      UPDATE users_in_bots SET (lang) = (_lang)
      WHERE bot_title = _bot_title AND user_id = local_user_id;
    ELSE
      INSERT INTO users_in_bots VALUES (_bot_title, local_user_id, _lang);
    END IF;

  END;
$$ LANGUAGE plpgsql;

-- check if the message length is less than 500, and replace user_id with local id
DROP FUNCTION insert_message(INTEGER, VARCHAR(4000), VARCHAR(50), INTEGER, INTEGER);
CREATE OR REPLACE FUNCTION insert_message(_msg_id INTEGER, _msg_text VARCHAR(4000), _date TIMESTAMP, _chat_id INTEGER, _user_id INTEGER) RETURNS VOID AS $$
  DECLARE
    local_user_id INTEGER := (SELECT local_id FROM users WHERE tg_id = _user_id);
  BEGIN
    -- check if the message length is less than 500
    IF char_length(_msg_text) > 500 THEN
      RETURN ;-- RAISE EXCEPTION 'Error inserting message: size of the text must be <= 500';
    END IF;

    -- check if the chat exists
    IF _chat_id NOT IN (SELECT chat_id FROM chats) THEN
      RAISE EXCEPTION 'Error inserting message: there is no chat with the given chat_id';
    END IF;

    -- if there is no such user - add it into the Users table
    IF _user_id NOT IN (SELECT tg_id FROM users) THEN
      INSERT INTO users (tg_id, first_name, last_name, username) VALUES (_user_id, NULL, NULL, NULL);
      local_user_id := (SELECT local_id FROM users WHERE tg_id = _user_id);
    END IF;

    -- if the message_in_chat exists - update it; otherwise - add new one
    IF (_msg_id, _chat_id, local_user_id) IN (SELECT msg_id, chat_id, user_id FROM messages) THEN
      UPDATE messages SET (text, date) = (_msg_text, _date)
      WHERE msg_id = _msg_id AND chat_id = _chat_id AND _user_id = local_user_id;
    ELSE
      INSERT INTO messages(msg_id, text, date, chat_id, user_id)  VALUES (_msg_id, _msg_text, _date, _chat_id, local_user_id);
    END IF;

  END;
$$ LANGUAGE plpgsql;

-- replace user_id with local id
-- SELECT * FROM insert_food_order(216842240, 'pizza', 'маргарита', '2017-02-15 15:45:19.173Z');
CREATE OR REPLACE FUNCTION insert_food_order(_user_id INTEGER, _food_category VARCHAR(100), _food_item VARCHAR(500), _quantity INTEGER, _order_timestamp TIMESTAMP) RETURNS VOID AS $$
  DECLARE
    local_user_id INTEGER := (SELECT local_id FROM users WHERE tg_id = _user_id);
  BEGIN

    -- check if the user exists
    IF _user_id NOT IN (SELECT tg_id FROM users) THEN
      INSERT INTO users (tg_id, first_name, last_name, username) VALUES (_user_id, NULL, NULL, NULL);
      local_user_id := (SELECT local_id FROM users WHERE tg_id = _user_id);
    END IF;

    -- insert new food order
    INSERT INTO food_orders(user_id, food_category, food_item, quantity, order_timestamp)
      VALUES (local_user_id, _food_category, _food_item, _quantity, _order_timestamp);

  END;
$$ LANGUAGE plpgsql;

-- replace user_id with local id
CREATE OR REPLACE FUNCTION insert_bus_click(_user_id INTEGER, _click_timestamp TIMESTAMP, _route_id VARCHAR(50), _route_start_time TIMESTAMP, _shuttle_id INTEGER) RETURNS VOID AS $$
  DECLARE
    local_user_id INTEGER := (SELECT local_id FROM users WHERE tg_id = _user_id);
  BEGIN

    -- check if the user exists
    IF _user_id NOT IN (SELECT tg_id FROM users) THEN
      INSERT INTO users (tg_id, first_name, last_name, username) VALUES (_user_id, NULL, NULL, NULL);
      local_user_id := (SELECT local_id FROM users WHERE tg_id = _user_id);
    END IF;

    INSERT INTO buses_clicks(user_id, click_timestamp, route_id, route_start_time, shuttle_id)
    VALUES (local_user_id, _click_timestamp, _route_id, _route_start_time, _shuttle_id);

  END;
$$ LANGUAGE plpgsql;

-- replace user_id with local id
CREATE OR REPLACE FUNCTION insert_placed_ad(_user_id INTEGER, _placed_timestamp TIMESTAMP, _category_title VARCHAR(15), _ad_type VARCHAR(15), _views_count INTEGER, _likes_count INTEGER) RETURNS VOID AS $$
  DECLARE
    local_user_id INTEGER := (SELECT local_id FROM users WHERE tg_id = _user_id);
  BEGIN

    -- check if the user exists
    IF _user_id NOT IN (SELECT tg_id FROM users) THEN
      INSERT INTO users (tg_id, first_name, last_name, username) VALUES (_user_id, NULL, NULL, NULL);
      local_user_id := (SELECT local_id FROM users WHERE tg_id = _user_id);
    END IF;

    INSERT INTO placed_ads(user_id, placed_timestamp, category_title, ad_type, views_count, likes_count)
    VALUES (local_user_id, _placed_timestamp, _category_title, _ad_type, _views_count, _likes_count);

  END;
$$ LANGUAGE plpgsql;

SELECT count(*) from users;

SELECT * FROM food_orders
NATURAL JOIN users WHERE users.local_id = food_orders.user_id and users.username = 'marashov_alexey';

SELECT user_id, food_category, food_item from food_orders;
SELECT * FROM users WHERE local_id = 9966;
SELECT * FROM users WHERE tg_id = 5997097;
SELECT count(*) FROM users WHERE first_name = 'was invited';
SELECT SUM(messages_count) FROM chats;