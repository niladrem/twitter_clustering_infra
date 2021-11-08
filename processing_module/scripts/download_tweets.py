import tweepy
import argparse
import os
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


def process_relation(relation_type, src_user_id, dst_user_id, text=None, tweet_id=None):
    relations_dict[relation_type].append(
        {"src_user_id": src_user_id, "dst_user_id": dst_user_id, "text": text, "tweet_id": tweet_id})


def process_post(api, post, extra_info):
    src_user_id = post.user.id
    if post.is_quote_status:
        status = api.lookup_statuses([post.quoted_status_id])[0]
        add_user(status.user)
        process_relation("quote", src_user_id, status.user.id, post.text, post.id)
    if post.retweeted:
        add_user(post.retweeted_status.user)
        process_relation("retweet", post.retweeted_status.user.id, src_user_id, post.text, post.id)
    if post.in_reply_to_status_id is not None:
        try:
            status = api.lookup_statuses([post.in_reply_to_status_id])[0]
            add_user(status.user)
            process_relation("reply", src_user_id, status.user.id, post.text, post.id)
        except:
            print("Could not find status with id", post.in_reply_to_status_id)
    for entity in post.entities['user_mentions']:
        if entity['id'] not in users_dict:
            mentioned_user = api.get_user(user_id=entity['id'])
            add_user(mentioned_user)
        process_relation("mention", src_user_id, entity['id'], post.text, post.id)

    if extra_info:
        retweeters = api.get_retweeter_ids(post.id)
        for retweeter in retweeters:
            if retweeter not in users_dict:
                r_user = api.get_user(user_id=retweeter)
                add_user(r_user)
            process_relation("retweet", src_user_id, retweeter, post.text, post.id)


def process_user(api, user_id, extra_info):
    # user timeline
    posts = api.user_timeline(user_id=user_id, count=200)
    for post in posts:
        process_post(api, post, extra_info)

    # favorites
    favorites = api.get_favorites(user_id=user_id, count=200)
    for favorite in favorites:
        process_relation("like", user_id, favorite)

    if extra_info:
        # followers
        followers = api.get_followers(user_id=user_id, count=200)
        for follower in followers:
            process_relation("follow", user_id, follower)

        # friends
        friends = api.get_friends(user_id=user_id, count=200)
        for friend in friends:
            process_relation("friend", user_id, friend)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--consumer-key')
    parser.add_argument('--consumer-secret')
    parser.add_argument('--access-token-key')
    parser.add_argument('--access-token-secret')
    parser.add_argument('--query', default='covid')
    parser.add_argument('--hours', type=int, default=3)
    parser.add_argument('--path', default="/shared/data/raw/")
    parser.add_argument('--extra-info', type=bool, default=False)
    parser.add_argument('--users-limit', type=int, default=15)

    args = parser.parse_args()

    auth = tweepy.OAuthHandler(args.consumer_key, args.consumer_secret)
    auth.set_access_token(args.access_token_key, args.access_token_secret)

    api = tweepy.API(auth, wait_on_rate_limit=True)

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

    while len(users_to_process) > 0 and len(processed_users) < args.users_limit:
        user = users_to_process.pop(0)
        if user not in processed_users:
            process_user(api, user, args.extra_info)
            processed_users.append(user)
            print("Processed users count: ", len(processed_users))

print("---USER DICT---")
print(users_dict)
print("---RELATIONS DICT---")
print(relations_dict)
print("---TO PROCESS---")
print(users_to_process)
uuid = str(uuid.uuid4())
with open(os.path.join(args.path, "relations_" + uuid), "wb") as result_file:
    pickle.dump(relations_dict, result_file)
with open(os.path.join(args.path, "users_" + uuid), "wb") as result_file:
    pickle.dump(users_dict, result_file)
