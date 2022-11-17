import os

os.environ["consumer_key"] = os.environ["TWITTER_API_KEY"]
os.environ["consumer_secret"] = os.environ["TWITTER_API_SECRET"]
os.environ["access_token"] = os.environ["TWITTER_ACCESS_TOKEN"]
os.environ["access_token_secret"] = os.environ["TWITTER_ACCESS_TOKEN_SECRET"]
os.environ['env_name']="development"

from twitivity import Activity

account_activity = Activity()
account_activity.register_webhook("https://fd27-143-198-221-207.ap.ngrok.io/webhooks/twitter")
account_activity.subscribe()

