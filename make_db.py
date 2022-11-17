"""CREATE sqlite DB script"""
import sqlite3
DB_NAME = "glyph_bot.db" # TODO make env

def create_twitter_user_db(c):
    # twitter id to wallet table
    tablename = "User"
    c.execute(f"""
    CREATE TABLE IF NOT EXISTS {tablename}(
        twitter_id,
        address TEXT UNIQUE NOT NULL
    )
    """)

def create_twitter_predictions_db(c):
    # twitter id to wallet table
    tablename = "TwitterPrediction"
    c.execute(f"""
    CREATE TABLE IF NOT EXISTS {tablename}(
        tweet_id,
        address,
        predicted_on,
        symbol,
        UNIQUE(address, predicted_on, symbol)
    )
    """)

def create_predictions_db(c):
    # twitter id to wallet table
    tablename = "Prediction"
    c.execute(f"""
    CREATE TABLE IF NOT EXISTS {tablename}(
        address,
        predicted_on,
        symbol,
        direction,
        duration,
        initial_price,
        initial_price_on,
        final_price,
        final_price_on,
        status,
        UNIQUE(address, predicted_on, symbol)
    )
    """)

def create_symbols_db(c):
    # twitter id to wallet table
    tablename = "Symbol"
    c.execute(f"""
    CREATE TABLE IF NOT EXISTS {tablename}(
        symbol UNIQUE,
        active
    )
    """)



def create_block_update_db(c):
    tablename = "ChainUpdate"
    c.execute(f"""
    CREATE TABLE IF NOT EXISTS {tablename}(
        last_updated_block_id
    )
    """)



def create_user_score_db(c):
    tablename = "Score"
    c.execute(f"""
    CREATE TABLE IF NOT EXISTS {tablename}(
        address UNIQUE,
        num_pending,
        num_completed,
        num_correct,
        avg_return
    )
    """)

if __name__ == '__main__':
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # predictions created, expired, completed
    create_predictions_db(c)
    # symbols active not active
    create_symbols_db(c)
    # UserScoreUpdated
    create_user_score_db(c)

    # tweet actions
    create_twitter_user_db(c)
    create_twitter_predictions_db(c)

    # db
    create_block_update_db(c)
