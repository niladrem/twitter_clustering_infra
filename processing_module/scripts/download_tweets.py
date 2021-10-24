# https://docs.tweepy.org/en/stable/api.html#get-tweet-timelines
import tweepy
import argparse
parser = argparse.ArgumentParser()

parser.add_argument('--consumer-key')
parser.add_argument('--consumer-secret')
parser.add_argument('--access-token-key')
parser.add_argument('--access-token-secret')
parser.add_argument('--query', default='covid')
parser.add_argument('--days', type=int, default=3)

args = parser.parse_args()

auth = tweepy.OAuthHandler(args.consumer_key, args.consumer_secret)
auth.set_access_token(args.access_token_key, args.access_token_secret)

api = tweepy.API(auth)

out = api.search_tweets("covid", lang="pl", result_type="recent", count=5)
for t in out:
  print(t._json)
