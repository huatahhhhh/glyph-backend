from  web3.auto import w3
from TwitterAPI import TwitterAPI
from twitterwebhooks import TwitterWebhookAdapter
import os
import json
from flask import Flask, request, abort
from eth_account.messages import encode_defunct

TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY', None)
TWITTER_API_SECRET = os.environ.get('TWITTER_API_SECRET', None)
ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN', None)
ACCESS_TOKEN_SECRET = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET', None)
TWITTER_HANDLE = os.environ.get('TWITTER_HANDLE', None)
TWITTER_ID = os.environ.get('TWITTER_ID', None)
ERROR_REPLY = "Sorry.. error encountered on bot :<"

app = Flask(__name__)

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
        return

    command = args[1].lower()
    if command == "register":
        verified, reply = _handle_register_flow(user_id, args)
        if not verified:
            reply_to_tweet(tweet_id, reply)
        reply_to_tweet(tweet_id, "You are verified :>")

    # elif args[1] in ("long", "short"):
        # symbol = args[2] 
        # if symbol not in SYMBOLS:
            # # TODO reply with error
            # return 

def _handle_register_flow(user_id, args):
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
            return False, "Invalid signature, please check your message"
        else:
            return True, ""
    except:
        return False, ERROR_REPLY

def get_tweet_text(tweet_id):
    # webhook does not have full text, use api to get the text instead
    twitter_api = get_twitter_api_v2()
    resp = twitter_api.request(f'tweets/:{tweet_id}')
    for item in resp:
        return item['text']
    return ''

def reply_to_tweet(tweet_id, message):
    # bot reply to tweet
    assert len(message) > 0
    twitter_api = get_twitter_api_v2()
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
    args = [arg for arg in args if arg]
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
 
# Once we have our event listeners configured, we can start the
# Flask server with the default `/events` endpoint on port 3000
if __name__ == '__main__':
    app.run(port=3000)
