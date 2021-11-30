import os
import shutil
import unittest
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from processing_module.scripts import download_tweets


class User:
    def __init__(self, id):
        self.id = id

    def __eq__(self, obj):
        return self.id == obj.id

    def wrap(self):
        return SimpleNamespace(user=self)


class Post:
    def __init__(self, id, text, user_id, created_at,
                 quoted_status_id=None, in_reply_to_status_id=None, retweeted_user_id=None, mentions=[]):
        self.id = id
        self.text = text
        self.user = User(user_id)
        self.created_at = created_at
        self.is_quote_status = False if quoted_status_id is None else True
        if quoted_status_id is not None:
            self.quoted_status_id = quoted_status_id
        self.in_reply_to_status_id = in_reply_to_status_id
        if retweeted_user_id:
            self.retweeted_status = User(retweeted_user_id).wrap()
        self.entities = {"user_mentions": [{"id": m} for m in mentions]}


class ApiMock:
    def __init__(self, time=None):
        self.query_counter = 0
        self.max_time = time

    def search_tweets(self, query, lang="en", result_type="recent", count=100, max_id=None, tweet_mode="extended"):
        self.query_counter += 1
        return [Post(1000 - self.query_counter, "", self.query_counter + 2137,
                     self.max_time - timedelta(hours=self.query_counter) if self.max_time
                     else datetime.now(timezone.utc))]

    def lookup_statuses(self, posts_id):
        return [User(id).wrap() for id in posts_id]

    def get_user(self, user_id):
        return User(user_id)

    def user_timeline(self, user_id=None, count=None):
        return [] if user_id == 2137 else\
            [Post(13, "test", user_id, download_tweets.process_time, retweeted_user_id=2137)]

    def get_favorites(self, user_id=None, count=None):
        return [User(3).wrap(), User(4).wrap()] if user_id == 2137 else []

    def get_followers(self, user_id=None, count=None):
        return [User(1), User(2)] if user_id == 2137 else []

    def get_friends(self, user_id=None, count=None):
        return [User(21)] if user_id == 2137 else []


class TestDownloadTweets(unittest.TestCase):
    def setUp(self):
        self.api = ApiMock()
        self.time = datetime.now(timezone.utc)
        self.created_at = self.time - timedelta(hours=1)
        download_tweets.process_time = self.time
        download_tweets.users_to_process = []
        download_tweets.users_dict = {}
        download_tweets.relations_dict = {"follow": [], "friend": [], "retweet": [], "mention": [], "like": [],
                                          "reply": [], "quote": []}

    def test_add_user(self):
        # given
        id = 2137

        # when
        user = User(id)
        download_tweets.add_user(user)

        # then
        self.assertEqual(download_tweets.users_to_process, [id])
        self.assertEqual(download_tweets.users_dict, {id: user})

    def test_process_simple_relation(self):
        # when
        download_tweets.process_relation("follow", 21, 37)

        # then
        self.assertEqual(download_tweets.relations_dict["follow"],
                         [{"src_user_id": 21, "dst_user_id": 37, "text": None, "tweet_id": None, "query": None,
                          "process_time": self.time, "created_at": None}])

    def test_process_full_relation(self):
        # given
        text = "abc"
        tweet_id = 2137

        # when
        download_tweets.process_relation("follow", 21, 37, text, tweet_id, self.created_at)

        # then
        self.assertEqual(download_tweets.relations_dict["follow"],
                         [{"src_user_id": 21, "dst_user_id": 37, "text": text, "tweet_id": tweet_id, "query": None,
                           "process_time": self.time, "created_at": self.created_at}])

    def test_process_user_no_posts_with_extra_info(self):
        # given
        user_id = 2137
        extra_info = True

        # when
        download_tweets.process_user(self.api, user_id, extra_info)

        # then
        users = [1, 2, 3, 4, 21]
        self.assertEqual(set(download_tweets.users_to_process), set(users))
        self.assertEqual(download_tweets.users_dict, {id: User(id) for id in users})
        self.assertEqual(download_tweets.relations_dict["follow"], [
            {"src_user_id": user_id, "dst_user_id": 1, "text": None, "tweet_id": None, "query": None,
             "process_time": self.time, "created_at": None},
            {"src_user_id": user_id, "dst_user_id": 2, "text": None, "tweet_id": None, "query": None,
             "process_time": self.time, "created_at": None}])
        self.assertEqual(download_tweets.relations_dict["friend"], [
            {"src_user_id": user_id, "dst_user_id": 21, "text": None, "tweet_id": None, "query": None,
             "process_time": self.time, "created_at": None}])
        self.assertEqual(download_tweets.relations_dict["like"], [
            {"src_user_id": user_id, "dst_user_id": 3, "text": None, "tweet_id": None, "query": None,
             "process_time": self.time, "created_at": None},
            {"src_user_id": user_id, "dst_user_id": 4, "text": None, "tweet_id": None, "query": None,
             "process_time": self.time, "created_at": None}])

    def test_process_user_no_posts_no_extra_info(self):
        # given
        user_id = 2137
        extra_info = False

        # when
        download_tweets.process_user(self.api, user_id, extra_info)

        # then
        users = [3, 4]
        self.assertEqual(set(download_tweets.users_to_process), set(users))
        self.assertEqual(download_tweets.users_dict, {id: User(id) for id in users})
        self.assertEqual(download_tweets.relations_dict["like"], [
            {"src_user_id": user_id, "dst_user_id": 3, "text": None, "tweet_id": None, "query": None,
             "process_time": self.time, "created_at": None},
            {"src_user_id": user_id, "dst_user_id": 4, "text": None, "tweet_id": None, "query": None,
             "process_time": self.time, "created_at": None}])

    def test_process_user_posts(self):
        # given
        user_id = 2138
        extra_info = False

        # when
        download_tweets.process_user(self.api, user_id, extra_info)

        # then
        self.assertEqual(set(download_tweets.users_to_process), set([2137]))
        self.assertEqual(download_tweets.users_dict, {2137: User(2137)})
        self.assertEqual(download_tweets.relations_dict["retweet"], [
            {"src_user_id": 2137, "dst_user_id": user_id, "text": None, "tweet_id": 13, "query": None,
             "process_time": self.time, "created_at": self.time}])

    def test_process_quoted_status(self):
        # given
        user_id = 2137
        text = "skandal"
        post_id = 21
        quoted_id = 13
        post = Post(post_id, text, user_id, self.created_at, quoted_status_id=quoted_id)

        # when
        download_tweets.process_post(self.api, post, False)

        # then
        self.assertEqual(download_tweets.users_to_process, [quoted_id])
        self.assertEqual(download_tweets.relations_dict["quote"], [
            {"src_user_id": user_id, "dst_user_id": quoted_id, "text": text, "tweet_id": post_id, "query": None,
             "process_time": self.time, "created_at": self.created_at}])

    def test_process_retweeted_status(self):
        # given
        user_id = 2137
        post_id = 21
        retweeted_id = 13
        post = Post(post_id, "text", user_id, self.created_at, retweeted_user_id=retweeted_id)

        # when
        download_tweets.process_post(self.api, post, False)

        # then
        self.assertEqual(download_tweets.users_to_process, [retweeted_id])
        self.assertEqual(download_tweets.relations_dict["retweet"], [
            {"src_user_id": retweeted_id, "dst_user_id": user_id, "text": None, "tweet_id": post_id, "query": None,
             "process_time": self.time, "created_at": self.created_at}])

    def test_process_reply_status(self):
        # given
        user_id = 2137
        post_id = 21
        reply_id = 37
        text = "skandal"
        post = Post(post_id, text, user_id, self.created_at, in_reply_to_status_id=reply_id)

        # when
        download_tweets.process_post(self.api, post, False)

        # then
        self.assertEqual(download_tweets.users_to_process, [reply_id])
        self.assertEqual(download_tweets.relations_dict["reply"], [
            {"src_user_id": user_id, "dst_user_id": reply_id, "text": text, "tweet_id": post_id, "query": None,
             "process_time": self.time, "created_at": self.created_at}])

    def test_process_mentions(self):
        # given
        user_id = 2137
        post_id = 21
        mention_id = 23
        text = "skandal"
        post = Post(post_id, text, user_id, self.created_at, mentions=[mention_id])

        # when
        download_tweets.process_post(self.api, post, False)

        # then
        self.assertEqual(download_tweets.users_to_process, [mention_id])
        self.assertEqual(download_tweets.relations_dict["mention"], [
            {"src_user_id": user_id, "dst_user_id": mention_id, "text": text, "tweet_id": post_id, "query": None,
             "process_time": self.time, "created_at": self.created_at}])


class TestMain(unittest.TestCase):
    def test_dump_files(self):
        # given
        download_tweets.users_dict = {}
        download_tweets.relations_dict = {"follow": [], "friend": [], "retweet": [], "mention": [], "like": [],
                                          "reply": [], "quote": []}
        uuid = "123"
        dir = "tmp"
        os.mkdir(dir)
        args = SimpleNamespace(path=dir)

        # when
        download_tweets.dump_files(args, uuid)

        # then
        self.assertEqual(os.listdir(dir), ["users_123", "relations_123"])
        shutil.rmtree(dir)

    def test_process_users_loop(self):
        # given
        api = ApiMock()
        download_tweets.users_to_process = [2137]
        download_tweets.users_dict = {}
        download_tweets.relations_dict = {"follow": [], "friend": [], "retweet": [], "mention": [], "like": [],
                                          "reply": [], "quote": []}
        download_tweets.processed_users = []
        args = SimpleNamespace(users_limit=3, extra_info=True)

        # when
        download_tweets.process_users_loop(args, api)

        # then
        self.assertEqual(len(download_tweets.processed_users), 3)

    def test_main_loop(self):
        # given
        api = ApiMock()
        args = SimpleNamespace(hours=5, users_limit=13)
        download_tweets.users_to_process = []

        # when
        download_tweets.main_loop(args, api)

        # then
        self.assertEqual(len(download_tweets.users_to_process), 13)

    def test_main_loop_with_time(self):
        # given
        time = datetime.now(timezone.utc) + timedelta(minutes=5)
        download_tweets.process_time = time
        api = ApiMock(time)
        args = SimpleNamespace(hours=5, users_limit=13)
        download_tweets.users_to_process = []

        # when
        download_tweets.main_loop(args, api)

        # then
        self.assertEqual(len(download_tweets.users_to_process), 5)


if __name__ == '__main__':
    unittest.main()
