from ipfs import write_to_ipfs
from datetime import datetime
import time
import sqlite3
from dateutil.relativedelta import relativedelta
from  web3.auto import w3
from TwitterAPI import TwitterAPI
from twitterwebhooks import TwitterWebhookAdapter
import os
import json
from flask import Flask, request, abort
from flask_cors import CORS
from eth_account.messages import encode_defunct
from contract import PredictContract, PriceFeedContract

TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY', None)
TWITTER_API_SECRET = os.environ.get('TWITTER_API_SECRET', None)
ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN', None)
ACCESS_TOKEN_SECRET = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET', None)
TWITTER_HANDLE = os.environ.get('TWITTER_HANDLE', None)
TWITTER_ID = os.environ.get('TWITTER_ID', None)
ERROR_REPLY = "Sorry.. error encountered on bot :<"
DB_NAME = "glyph_bot.db"

app = Flask(__name__)
CORS(app)

events_adapter = TwitterWebhookAdapter(TWITTER_API_SECRET, "/webhooks/twitter", app)

#logger = events_adapter.server.logger
def get_twitter_api_v1():
    twitter_api = TwitterAPI(TWITTER_API_KEY, TWITTER_API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

def get_twitter_api_v2():
    return TwitterAPI(TWITTER_API_KEY, TWITTER_API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, api_version='2')

def get_account_id():
    # Helper for fetching the bot's ID
    twitter_api = get_twitter_api_v1()
    credentials = twitter_api.request('account/verify_credentials').json()
    return credentials['id']

@events_adapter.on("tweet_create_events")
def handle_message(event_data):
    tweet_obj = event_data['event']
    tweet_id = tweet_obj['id']
    user_id = tweet_obj['user']['id']
    user_name = tweet_obj['user']['screen_name']
     
    if str(user_id) == str(TWITTER_ID):
        print("received own event")
        return

    print(tweet_id)
    tweet_text = get_tweet_text(tweet_id)
    timestamp = tweet_obj['timestamp_ms']

    print('tweet text:')
    print(tweet_text)
    args = parse_message(tweet_text)

    if args[0] != TWITTER_HANDLE:
        print("got different handle", args[0])
        if args[1] == TWITTER_HANDLE:
            args = args[1:]
        else:
            return

    command = args[1].lower()
    if command == "register":
        _handle_register_flow(tweet_id, user_id, user_name, args)
        return

    elif args[1].lower() in ("long", "short"):
        _handle_predict_flow(tweet_id, user_id, user_name, args, tweet_text)
        return

def _get_address(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    result = c.execute(f"SELECT * FROM User WHERE twitter_id={user_id}").fetchone()
    conn.close()
    return result[1]

def _handle_predict_flow(tweet_id, user_id, user_name, args, tweet_text):
    """@bot [long,short] [usd] [3M,1Y,1d,1h]

    H D M Y 
    """
    address = _get_address(user_id)
    if not address:
        reply_to_tweet(tweet_id, user_name, "You are not registered, please register first")

    direction = args[1].upper()
    if direction == "LONG":
        direction = True
    elif direction == "SHORT":
        direction = False
    else:
        reply_to_tweet(tweet_id, user_name, "Direction must be 'long' or 'short'")

    # check if symbol is active
    symbol = args[2].upper()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    result = c.execute(f"SELECT * FROM Symbol WHERE symbol='{symbol}'").fetchall()
    conn.close()
    symbol_invalid = False
    if len(result) == 1:
        if not int(result[0][1]):
            symbol_invalid = True
    else:
        symbol_invalid = True

    if symbol_invalid:
        reply_to_tweet(tweet_id, user_name, f"Symbol {symbol} is not valid")
        return 
    
    # parse datetime
    horizon = args[3].upper()
    if len(horizon) < 2:
        reply_to_tweet(tweet_id, user_name, f"Invalid duration - {horizon}")
        return 

    timeunit = horizon[-1]

    units = {
        'H': relativedelta(hours=1),
        'D': relativedelta(days=1),
        'M': relativedelta(months=1),
        'W': relativedelta(weeks=1),
        'Y': relativedelta(years=1)
    }
    if timeunit not in units.keys():
        reply_to_tweet(tweet_id, user_name, f"Invalid duration - {horizon}")
        return
    else:
        unit = units[timeunit]
    try:
        scalar = int(horizon[:-1])
        duration = scalar * unit
    except ValueError:
        reply_to_tweet(tweet_id, user_name, f"Invalid duration - {horizon}")
        return
    dt_now = datetime.now()
    duration = int(((dt_now + duration) - dt_now).total_seconds())

    # prediction time
    pred_at = int(time.time())

    print(address, pred_at, symbol, direction, duration, "na")
    ipfs_data = dict(tweet_id=tweet_id, twitter_user_id=user_id, twitter_username=f"@{user_name}", tweet=tweet_text)
    ipfscid = write_to_ipfs(ipfs_data)
    tx = PredictContract.create_prediction(
            address,
            pred_at,
            symbol,
            direction,
            duration,
            str(ipfscid)
    )
    success_reply_to_tweet(tweet_id, user_name, "created prediction", tx)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO TwitterPrediction VALUES ({tweet_id}, '{address}', {pred_at}, '{symbol}')")
    conn.commit()



def _handle_register_flow(tweet_id, user_id, user_name, args):
    try:
        if len(args) < 4:
            print(args)
            return False, "Not enough arguments for register - expected 4, delete tweet and try again"
        ## verify signature
        wallet = args[2]
        signature = args[3]
        message = encode_defunct(text=str(user_id)) # we expect user's twitter id to be encoded
        got_wallet = w3.eth.account.recover_message(message, signature=signature)
        if wallet != got_wallet:
            reply_to_tweet(tweet_id, user_name, "Invalid signature, please check your message")
            return 
        else:
            # check if user is registered
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            
            exists = c.execute(f"SELECT * FROM User WHERE twitter_id={user_id}").fetchall()
            if len(exists) == 0:
                c.execute(f"INSERT INTO User VALUES ({user_id}, '{wallet}')")
                conn.commit()
            conn.close()

            tx = PredictContract.add_user(wallet)
            success_reply_to_tweet(tweet_id, user_name, "registered wallet", tx)

    except Exception as e:
        print(e)
        reply_to_tweet(tweet_id, user_name, ERROR_REPLY)

def get_tweet_text(tweet_id):
    # webhook does not have full text, use api to get the text instead
    twitter_api = get_twitter_api_v2()
    resp = twitter_api.request(f'tweets/:{tweet_id}')
    for item in resp:
        return item['text']
    return ''

def success_reply_to_tweet(tweet_id, user_name, event, tx):
    # event should be <verb> <noun>
    # e.g created prediction, added user
    url = f'https://mumbai.polygonscan.com/tx/{tx}'
    message = f"Successfully {event}!! :>\nTransaction URL: {url}"
    reply_to_tweet(tweet_id, user_name, message)

def reply_to_tweet(tweet_id, user_name, message):
    # bot reply to tweet
    assert len(message) > 0
    twitter_api = get_twitter_api_v2()

    prefix = f""
    if user_name:
        prefix = f"@{user_name} "

    message = f"{prefix}{message}"
    data = {
        'reply': {
            'in_reply_to_tweet_id': str(tweet_id)
        },
        'text': message
    }
    r = twitter_api.request('tweets', method_override="POST", params=data)

def parse_message(message: str):
    """
    LONG SYMBOL
    """
    valid = False
    message = message.strip()
    args = message.split(' ')
    args = [arg.strip() for arg in args if arg]
    return args

# @events_adapter.on("any")
# def handle_message(event_data):
    # # Loop through events array and log received events
    # for s in filter(lambda x: '_event' in x, list(event_data)):
        # print("[any] Received event: {}".format(s))
        # print(json.dumps(event_data, indent=4, sort_keys=True))

# Handler for error events
@events_adapter.on("error")
def error_handler(err):
    print("ERROR: " + str(err))

# Flask Routes ------------------------------------------------------------------------------

@app.route("/twitter/userlookup")
def twitter_user_lookup():
    twitter_api = get_twitter_api_v2()
    handle = request.args.get("handle")
    url = f"users/by/username/:{handle}"
    try:
        resp = twitter_api.request(url)
        for item in resp:
            return item
    except Exception:
        abort(404)
    abort(404)

@app.route("/glyph/isuser/")
def wallet_lookup():
    wallet = request.args.get("address")
    return {'result': PredictContract.is_user(wallet)}

 
 
# Once we have our event listeners configured, we can start the
# Flask server with the default `/events` endpoint on port 3000
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3000)
    # app.run(port=3000)
