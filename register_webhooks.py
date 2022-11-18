import os

os.environ["consumer_key"] = os.environ["TWITTER_API_KEY"]
os.environ["consumer_secret"] = os.environ["TWITTER_API_SECRET"]
os.environ["access_token"] = os.environ["TWITTER_ACCESS_TOKEN"]
os.environ["access_token_secret"] = os.environ["TWITTER_ACCESS_TOKEN_SECRET"]
os.environ['env_name']="development"

from twitivity import Activity

account_activity = Activity()

# existing = account_activity.webhooks()

# # Delete existing webhooks
# import json
# print(json.dumps(existing, indent=2))
# try:
    # existing = existing['environments'][0]['webhooks'][0]['id']
# except:
    # existing = False
# if existing:
    # account_activity.delete(existing)

# create new webhook
account_activity.register_webhook("https://313f-143-198-221-207.ap.ngrok.io/webhooks/twitter")
# account_activity.register_webhook("https://143.198.221.207:3000")
resp = account_activity.subscribe()

print(resp.json())

