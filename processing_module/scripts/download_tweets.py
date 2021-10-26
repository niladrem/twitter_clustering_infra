import tweepy
import argparse
import pickle
import uuid
from datetime import datetime, timedelta, timezone

parser = argparse.ArgumentParser()

parser.add_argument('--consumer-key')
parser.add_argument('--consumer-secret')
parser.add_argument('--access-token-key')
parser.add_argument('--access-token-secret')
parser.add_argument('--query', default='covid')
parser.add_argument('--hours', type=int, default=3)
parser.add_argument('--path', default="/shared/data/json/")

args = parser.parse_args()

auth = tweepy.OAuthHandler(args.consumer_key, args.consumer_secret)
auth.set_access_token(args.access_token_key, args.access_token_secret)

api = tweepy.API(auth)

min_date = datetime.now(timezone.utc) - timedelta(hours=args.hours)
curr_date = datetime.now(timezone.utc)
max_id = None
results = []
while curr_date > min_date:
  out = api.search_tweets(args.query, lang="pl", result_type="recent", count=100, max_id=max_id)
  for t in out:
    max_id = t.id if max_id is None else min(max_id, t.id)
    curr_date = t.created_at
    if curr_date > min_date:
      results.append(t)

filename = str(uuid.uuid4())
with open(args.path + filename, "wb") as result_file:
  pickle.dump(results, result_file)


