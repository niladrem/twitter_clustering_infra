import os
import pandas as pd
import pickle
import shutil
import unittest
from types import SimpleNamespace
from processing_module.scripts import parse_tweets


class User:
    def __init__(self, screen_name, followers_count, friends_count, favourites_count):
        self.screen_name = screen_name
        self.followers_count = followers_count
        self.friends_count = friends_count
        self.favourites_count = favourites_count


class TestParseTweets(unittest.TestCase):
    def test_process_users_dict(self):
        # given
        parse_tweets.users = []
        users_dict = {1: User("1", 2, 3, 4), 2: User("2", 3, 4, 5)}

        # when
        parse_tweets.process_users_dict(users_dict)

        # then
        self.assertEqual(parse_tweets.users, [tuple([1, "1", 2, 3, 4]), tuple([2, "2", 3, 4, 5])])

    def test_process_relations_dict(self):
        # given
        parse_tweets.relations = []
        relations_dict = {
            "a": [
                {"src_user_id": 1, "dst_user_id": 2, "text": "3", "tweet_id": 4, "query": "5",
                 "process_time": 6, "created_at": 7},
                {"src_user_id": 11, "dst_user_id": 12, "text": "13", "tweet_id": 14, "query": "15",
                 "process_time": 16, "created_at": 17}
            ], "b": [
                {"src_user_id": 21, "dst_user_id": 22, "text": "23", "tweet_id": 24, "query": "25",
                 "process_time": 26, "created_at": 27}
            ]}

        # when
        parse_tweets.process_relations_dict(relations_dict)

        # then
        self.assertEqual(parse_tweets.relations, [
            tuple([1, 2, 4, "a", "3", "5", 6, 7]),
            tuple([11, 12, 14, "a", "13", "15", 16, 17]),
            tuple([21, 22, 24, "b", "23", "25", 26, 27])
        ])


class TestHelpers(unittest.TestCase):
    def test_dump_files(self):
        # given
        suffix = 123
        dir = "tmp"
        os.mkdir(dir)
        df = pd.DataFrame(data={'col1': [1, 2], 'col2': [3, 4]})
        args = SimpleNamespace(output_path=dir)

        # when
        parse_tweets.dump_files(args, suffix, df, df)

        # then
        self.assertEqual(os.listdir(dir), ["users_123.csv", "relations_123.csv"])
        shutil.rmtree(dir)

    def test_main_loop(self):
        # given
        parse_tweets.relations = []
        parse_tweets.users = []
        in_dir = "in_tmp"
        uuid = "123"
        os.mkdir(in_dir)
        users_dict = {1: User("1", 2, 3, 4), 2: User("2", 3, 4, 5)}
        relations_dict = {
            "b": [
                {"src_user_id": 21, "dst_user_id": 22, "text": "23", "tweet_id": 24, "query": "25",
                 "process_time": 26, "created_at": 27}
            ]}
        with open(os.path.join(in_dir, "relations_" + uuid), "wb") as result_file:
            pickle.dump(relations_dict, result_file)
        with open(os.path.join(in_dir, "users_" + uuid), "wb") as result_file:
            pickle.dump(users_dict, result_file)
        args = SimpleNamespace(input_path=in_dir, remove_processed_files=True)

        # when
        parse_tweets.main_loop(args)

        # then
        self.assertEqual(parse_tweets.users, [tuple([1, "1", 2, 3, 4]), tuple([2, "2", 3, 4, 5])])
        self.assertEqual(parse_tweets.relations, [tuple([21, 22, 24, "b", "23", "25", 26, 27])])
        self.assertEqual(os.listdir(in_dir), [])
        os.rmdir(in_dir)


if __name__ == '__main__':
    unittest.main()
