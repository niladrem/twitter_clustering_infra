import time
import tweepy
import argparse
import pickle
import uuid
from datetime import datetime, timedelta, timezone

users_dict = {}
relations_dict = {"follow": [], "friend": [], "retweet": [], "mention": [], "like": [], "reply": [], "quote": []}
users_to_process = []
processed_users = []


def add_user(user):
    users_to_process.append(user.id)
    users_dict[user.id] = user


def process_simple_relation(relation_type, src_user_id, dst_user_id, text):
    relations_dict[relation_type].append({"src_user_id": src_user_id, "dst_user_id": dst_user_id, "text": text})


def process_post(api, post):
    # quote - response/retweet?
    src_user_id = post.user.id
    if post.is_quote_status:
        status = api.lookup_statuses([post.quoted_status_id])[0]
        add_user(status.user)
        process_simple_relation("quote", src_user_id, status.user.id, post.text)
    if post.retweeted:
        add_user(post.retweeted_status.user)
        process_simple_relation("retweet", post.retweeted_status.user.id, src_user_id, post.text)
    if post.in_reply_to_status_id is not None:
        status = api.lookup_statuses([post.in_reply_to_status_id])[0]
        add_user(status.user)
        process_simple_relation("reply", src_user_id, status.user.id, post.text)
    for entity in post.entities['user_mentions']:
        mentioned_user = api.get_user(entity.id)
        add_user(mentioned_user)
        process_simple_relation("mention", src_user_id, user.id, post.text)


    # get retweeters @TODO
    print(post)


def process_user(api, user_id, extra_info):
    # user timeline
    posts = api.user_timeline(user_id=user_id, count=200)
    for post in posts:
        process_post(api, post)

    # favorites
    favorites = api.get_favorites(user_id=user_id, count=200)
    for favorite in favorites:
        process_simple_relation("like", user_id, favorite, None)

    if extra_info:
        # followers
        followers = api.get_followers(user_id=user_id, count=200)
        for follower in followers:
            process_simple_relation("follow", user_id, follower, None)

        # friends
        friends = api.get_friends(user_id=user_id, count=200)
        for friend in friends:
            process_simple_relation("friend", user_id, friend, None)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--consumer-key')
    parser.add_argument('--consumer-secret')
    parser.add_argument('--access-token-key')
    parser.add_argument('--access-token-secret')
    parser.add_argument('--query', default='covid')
    parser.add_argument('--hours', type=int, default=3)
    parser.add_argument('--path', default="/shared/data/json/")
    parser.add_argument('--extra-info', type=bool, default=False)

    args = parser.parse_args()

    auth = tweepy.OAuthHandler(args.consumer_key, args.consumer_secret)
    auth.set_access_token(args.access_token_key, args.access_token_secret)

    api = tweepy.API(auth)

    min_date = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    curr_date = datetime.now(timezone.utc)
    max_id = None

    while curr_date > min_date:
        out = api.search_tweets(args.query, lang="pl", result_type="recent", count=100, max_id=max_id,
                                tweet_mode="extended")
        for t in out:
            max_id = t.id if max_id is None else min(max_id, t.id)
            curr_date = t.created_at
            if curr_date > min_date:
                users_to_process.append(t.user.id)
                users_dict[t.user.id] = t.user
        break

    while len(users_to_process) > 0 and len(processed_users) < 1:
        user = users_to_process.pop(0)
        if user not in processed_users:
            process_user(api, user, args.extra_info)
            processed_users.append(user)

print("---USER DICT---")
print(users_dict)
print("---RELATIONS DICT---")
print(relations_dict)
print("---TO PROCESS---")
print(users_to_process)
# filename = str(uuid.uuid4())
# with open(args.path + filename, "wb") as result_file:
#   pickle.dump(results, result_file)
