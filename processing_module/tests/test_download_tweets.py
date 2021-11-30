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


class TestHelpClasses(unittest.TestCase):
    def test_user(self):
        # given
        id = 2137

        # when
        user = User(id)
        user2 = User(id)
        wrapped = user.wrap()

        # then
        self.assertEqual(user.id, id)
        self.assertEqual(user, user2)
        self.assertEqual(wrapped, SimpleNamespace(user=user))

    def test_post(self):
        # given
        post_id = 2137
        content = "test"
        user_id = 7321
        quoted_id = 21
        in_reply_id = 37
        retweeted_id = 23
        mention = 33
        time = datetime.now(timezone.utc)

        # when
        post = Post(post_id, content, user_id, time, quoted_id, in_reply_id, retweeted_id, [mention])

        # then
        self.assertEqual(post.id, post_id)
        self.assertEqual(post.user.id, user_id)
        self.assertEqual(post.text, content)
        self.assertEqual(post.created_at, time)
        self.assertEqual(post.is_quote_status, True)
        self.assertEqual(post.quoted_status_id, quoted_id)
        self.assertEqual(post.in_reply_to_status_id, in_reply_id)
        self.assertEqual(post.retweeted_status.user.id, retweeted_id)
        self.assertEqual(post.entities["user_mentions"][0]["id"], mention)


class TestDownloadTweets(unittest.TestCase):
    def test_add_user(self):
        # given
        download_tweets.users_to_process = []
        download_tweets.users_dict = {}
        id = 2137

        # when
        user = User(id)
        download_tweets.add_user(user)

        # then
        self.assertEqual(download_tweets.users_to_process, [id])
        self.assertEqual(download_tweets.users_dict, {id: user})

    def test_process_simple_relation(self):
        # given
        download_tweets.relations_dict = {"follow": [], "friend": [], "retweet": [], "mention": [], "like": [],
                                          "reply": [], "quote": []}
        time = datetime.now(timezone.utc)
        download_tweets.process_time = time

        # when
        download_tweets.process_relation("follow", 21, 37)

        # then
        self.assertEqual(download_tweets.relations_dict["follow"],
                         [{"src_user_id": 21, "dst_user_id": 37, "text": None, "tweet_id": None, "query": None,
                          "process_time": time, "created_at": None}])

    def test_process_full_relation(self):
        # given
        download_tweets.relations_dict = {"follow": [], "friend": [], "retweet": [], "mention": [], "like": [],
                                          "reply": [], "quote": []}
        text = "abc"
        tweet_id = 2137
        time = datetime.now(timezone.utc)
        created_at = time - timedelta(hours=1)
        download_tweets.process_time = time

        # when
        download_tweets.process_relation("follow", 21, 37, text, tweet_id, created_at)

        # then
        self.assertEqual(download_tweets.relations_dict["follow"],
                         [{"src_user_id": 21, "dst_user_id": 37, "text": text, "tweet_id": tweet_id, "query": None,
                           "process_time": time, "created_at": created_at}])

    def test_process_user_no_posts_with_extra_info(self):
        # given
        api = ApiMock()
        user_id = 2137
        extra_info = True
        time = datetime.now(timezone.utc)
        download_tweets.process_time = time
        download_tweets.users_to_process = []
        download_tweets.users_dict = {}
        download_tweets.relations_dict = {"follow": [], "friend": [], "retweet": [], "mention": [], "like": [],
                                          "reply": [], "quote": []}

        # when
        download_tweets.process_user(api, user_id, extra_info)

        # then
        users = [1, 2, 3, 4, 21]
        self.assertEqual(set(download_tweets.users_to_process), set(users))
        self.assertEqual(download_tweets.users_dict, {id: User(id) for id in users})
        self.assertEqual(download_tweets.relations_dict["retweet"], [])
        self.assertEqual(download_tweets.relations_dict["mention"], [])
        self.assertEqual(download_tweets.relations_dict["reply"], [])
        self.assertEqual(download_tweets.relations_dict["quote"], [])
        self.assertEqual(download_tweets.relations_dict["follow"], [
            {"src_user_id": user_id, "dst_user_id": 1, "text": None, "tweet_id": None, "query": None,
             "process_time": time, "created_at": None},
            {"src_user_id": user_id, "dst_user_id": 2, "text": None, "tweet_id": None, "query": None,
             "process_time": time, "created_at": None}])
        self.assertEqual(download_tweets.relations_dict["friend"], [
            {"src_user_id": user_id, "dst_user_id": 21, "text": None, "tweet_id": None, "query": None,
             "process_time": time, "created_at": None}])
        self.assertEqual(download_tweets.relations_dict["like"], [
            {"src_user_id": user_id, "dst_user_id": 3, "text": None, "tweet_id": None, "query": None,
             "process_time": time, "created_at": None},
            {"src_user_id": user_id, "dst_user_id": 4, "text": None, "tweet_id": None, "query": None,
             "process_time": time, "created_at": None}])

    def test_process_user_no_posts_no_extra_info(self):
        # given
        api = ApiMock()
        user_id = 2137
        extra_info = False
        time = datetime.now(timezone.utc)
        download_tweets.process_time = time
        download_tweets.users_to_process = []
        download_tweets.users_dict = {}
        download_tweets.relations_dict = {"follow": [], "friend": [], "retweet": [], "mention": [], "like": [],
                                          "reply": [], "quote": []}

        # when
        download_tweets.process_user(api, user_id, extra_info)

        # then
        users = [3, 4]
        self.assertEqual(set(download_tweets.users_to_process), set(users))
        self.assertEqual(download_tweets.users_dict, {id: User(id) for id in users})
        self.assertEqual(download_tweets.relations_dict["retweet"], [])
        self.assertEqual(download_tweets.relations_dict["mention"], [])
        self.assertEqual(download_tweets.relations_dict["reply"], [])
        self.assertEqual(download_tweets.relations_dict["quote"], [])
        self.assertEqual(download_tweets.relations_dict["follow"], [])
        self.assertEqual(download_tweets.relations_dict["friend"], [])
        self.assertEqual(download_tweets.relations_dict["like"], [
            {"src_user_id": user_id, "dst_user_id": 3, "text": None, "tweet_id": None, "query": None,
             "process_time": time, "created_at": None},
            {"src_user_id": user_id, "dst_user_id": 4, "text": None, "tweet_id": None, "query": None,
             "process_time": time, "created_at": None}])

    def test_process_user_posts(self):
        # given
        api = ApiMock()
        user_id = 2138
        extra_info = False
        time = datetime.now(timezone.utc)
        download_tweets.process_time = time
        download_tweets.users_to_process = []
        download_tweets.users_dict = {}
        download_tweets.relations_dict = {"follow": [], "friend": [], "retweet": [], "mention": [], "like": [],
                                          "reply": [], "quote": []}

        # when
        download_tweets.process_user(api, user_id, extra_info)

        # then
        self.assertEqual(set(download_tweets.users_to_process), set([2137]))
        self.assertEqual(download_tweets.users_dict, {2137: User(2137)})
        self.assertEqual(download_tweets.relations_dict["retweet"], [
            {"src_user_id": 2137, "dst_user_id": user_id, "text": None, "tweet_id": 13, "query": None,
             "process_time": time, "created_at": time}])
        self.assertEqual(download_tweets.relations_dict["mention"], [])
        self.assertEqual(download_tweets.relations_dict["reply"], [])
        self.assertEqual(download_tweets.relations_dict["quote"], [])
        self.assertEqual(download_tweets.relations_dict["follow"], [])
        self.assertEqual(download_tweets.relations_dict["friend"], [])
        self.assertEqual(download_tweets.relations_dict["like"], [])

    def test_process_quoted_status(self):
        # given
        api = ApiMock()
        time = datetime.now(timezone.utc)
        download_tweets.process_time = time
        created_at = time - timedelta(hours=1)
        download_tweets.users_to_process = []
        download_tweets.relations_dict = {"follow": [], "friend": [], "retweet": [], "mention": [], "like": [],
                                          "reply": [], "quote": []}
        user_id = 2137
        text = "skandal"
        post_id = 21
        quoted_id = 13
        post = Post(post_id, text, user_id, created_at, quoted_status_id=quoted_id)

        # when
        download_tweets.process_post(api, post, False)

        # then
        self.assertEqual(download_tweets.users_to_process, [quoted_id])
        self.assertEqual(download_tweets.relations_dict["quote"], [
            {"src_user_id": user_id, "dst_user_id": quoted_id, "text": text, "tweet_id": post_id, "query": None,
             "process_time": time, "created_at": created_at}])

    def test_process_retweeted_status(self):
        # given
        api = ApiMock()
        time = datetime.now(timezone.utc)
        download_tweets.process_time = time
        created_at = time - timedelta(hours=1)
        download_tweets.users_to_process = []
        download_tweets.relations_dict = {"follow": [], "friend": [], "retweet": [], "mention": [], "like": [],
                                          "reply": [], "quote": []}
        user_id = 2137
        post_id = 21
        retweeted_id = 13
        post = Post(post_id, "text", user_id, created_at, retweeted_user_id=retweeted_id)

        # when
        download_tweets.process_post(api, post, False)

        # then
        self.assertEqual(download_tweets.users_to_process, [retweeted_id])
        self.assertEqual(download_tweets.relations_dict["retweet"], [
            {"src_user_id": retweeted_id, "dst_user_id": user_id, "text": None, "tweet_id": post_id, "query": None,
             "process_time": time, "created_at": created_at}])

    def test_process_reply_status(self):
        # given
        api = ApiMock()
        time = datetime.now(timezone.utc)
        download_tweets.process_time = time
        created_at = time - timedelta(hours=1)
        download_tweets.users_to_process = []
        download_tweets.relations_dict = {"follow": [], "friend": [], "retweet": [], "mention": [], "like": [],
                                          "reply": [], "quote": []}
        user_id = 2137
        post_id = 21
        reply_id = 37
        text = "skandal"
        post = Post(post_id, text, user_id, created_at, in_reply_to_status_id=reply_id)

        # when
        download_tweets.process_post(api, post, False)

        # then
        self.assertEqual(download_tweets.users_to_process, [reply_id])
        self.assertEqual(download_tweets.relations_dict["reply"], [
            {"src_user_id": user_id, "dst_user_id": reply_id, "text": text, "tweet_id": post_id, "query": None,
             "process_time": time, "created_at": created_at}])

    def test_process_mentions(self):
        # given
        api = ApiMock()
        time = datetime.now(timezone.utc)
        download_tweets.process_time = time
        created_at = time - timedelta(hours=1)
        download_tweets.users_to_process = []
        download_tweets.relations_dict = {"follow": [], "friend": [], "retweet": [], "mention": [], "like": [],
                                          "reply": [], "quote": []}
        user_id = 2137
        post_id = 21
        mention_id = 23
        text = "skandal"
        post = Post(post_id, text, user_id, created_at, mentions=[mention_id])

        # when
        download_tweets.process_post(api, post, False)

        # then
        self.assertEqual(download_tweets.users_to_process, [mention_id])
        self.assertEqual(download_tweets.relations_dict["mention"], [
            {"src_user_id": user_id, "dst_user_id": mention_id, "text": text, "tweet_id": post_id, "query": None,
             "process_time": time, "created_at": created_at}])


if __name__ == '__main__':
    unittest.main()
