import unittest
from datetime import datetime, timezone, timedelta
from processing_module.scripts import download_tweets


class User:
    def __init__(self, id):
        self.id = id


class Post:
    pass


class ApiMock:
    def lookup_statuses(self, post_id):
        pass

    def user_timeline(self, user_id=None, count=None):
        return [] if user_id == 2137 else [Post()]

    def get_favorites(self, user_id=None, count=None):
        return [User(3), User(4)]

    def get_followers(self, user_id=None, count=None):
        return [User(1), User(2)]


class TestHelpClasses(unittest.TestCase):
    def test_user(self):
        # given
        id = 2137

        # when
        user = User(id)

        # then
        self.assertEqual(user.id, id)


class TestSimpleProcessing(unittest.TestCase):
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
        download_tweets.relations_dict = {"follow": [], "friend": [], "retweet": [], "mention": [], "like": [], "reply": [], "quote": []}
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


if __name__ == '__main__':
    unittest.main()
