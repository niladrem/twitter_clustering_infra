import pandas as pd
import psycopg2
import testing.postgresql
import unittest
from datetime import datetime, timezone
from processing_module.scripts import insert_into_postgres


class TestInsertIntoPostgres(unittest.TestCase):
    def setUp(self):
        self.postgresql = testing.postgresql.Postgresql()
        self.conn = psycopg2.connect(**self.postgresql.dsn())
        cur = self.conn.cursor()
        cur.execute(self.get_create_users())
        cur.execute(self.get_create_relations())
        self.conn.commit()
        cur.close()

    def tearDown(self):
        self.conn.close()
        self.postgresql.stop()

    @staticmethod
    def get_create_users():
        return """CREATE TABLE users (
            id VARCHAR(30) PRIMARY KEY,
            screen_name VARCHAR(50),
            followers_count INTEGER,
            friends_count INTEGER,
            favourites_count INTEGER
        );"""

    @staticmethod
    def get_create_relations():
        return """CREATE TABLE relations (
            id SERIAL PRIMARY KEY,
            id_source VARCHAR(30),
            id_destination VARCHAR(30),
            tweet_id VARCHAR(30),
            type VARCHAR(10),
            content TEXT,
            query VARCHAR(50),
            process_time TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE
        );"""

    def test_insert_users(self):
        # given
        df = pd.DataFrame(data={"id": [2], "screen_name": ["1"], "followers_count": [3], "friends_count": [7],
                                "favourites_count": [7]})
        cur = self.conn.cursor()

        # when
        insert_into_postgres.process_users_df(cur, df, "users")
        self.conn.commit()

        # then
        cur.execute("SELECT * FROM users")
        rows = cur.fetchall()
        self.assertEqual(rows, [("2", "1", 3, 7, 7)])

    def test_insert_relations(self):
        # given
        dt = datetime.now(timezone.utc)
        df = pd.DataFrame(data={"id_source": [2, 1], "id_destination": [3, 7], "tweet_id": [21, 37],
                                "type": ["follow", "like"], "text": [None, None], "query": ["21", "37"],
                                "process_time": [dt, dt], "created_at": [None, None]})
        cur = self.conn.cursor()

        # when
        insert_into_postgres.process_relations_df(cur, df, "relations")
        self.conn.commit()

        # then
        cur.execute("SELECT * FROM relations")
        rows = cur.fetchall()
        self.assertEqual(rows, [(1, "2", "3", "21", "follow", None, "21", dt, None),
                                (2, "1", "7", "37", "like", None, "37", dt, None)])


if __name__ == '__main__':
    unittest.main()
