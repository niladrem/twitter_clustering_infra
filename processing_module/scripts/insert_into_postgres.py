import argparse
import os
import pandas as pd
import psycopg2


def process_users_df(cur, users_df, table_name):
    print("----users-----")
    query = "INSERT INTO " + table_name + " VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING;"
    cur.executemany(query, list(users_df.itertuples(index=False, name=None)))
    print("success")


def process_relations_df(cur, relations_df, table_name):
    print("----relations-----")
    query = "INSERT INTO " + table_name + " (id_source, id_destination, tweet_id, type, content) " \
                                          "VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING;"
    cur.executemany(query, list(relations_df.where(pd.notnull(relations_df), None).itertuples(index=False, name=None)))
    print("success")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--path', default='/shared/data/formatted/')
    parser.add_argument('--remove-processed-files', type=bool, default=False)
    parser.add_argument('--postgres-host', default='localhost')
    parser.add_argument('--postgres-port', default='5432')
    parser.add_argument('--postgres-login', default='twitter')
    parser.add_argument('--postgres-password', default='twitter')
    parser.add_argument('--postgres-database', default='twitter')
    parser.add_argument('--postgres-users', default='public.users')
    parser.add_argument('--postgres-relations', default='public.relations')

    args = parser.parse_args()

    conn = psycopg2.connect(host=args.postgres_host, database=args.postgres_database, port=args.postgres_port,
                            user=args.postgres_login, password=args.postgres_password)

    cur = conn.cursor()

    files = os.listdir(args.path)
    for file in reversed(files):
        try:
            if "users" in file:
                process_users_df(cur,
                                 pd.read_csv(os.path.join(args.path, file),
                                             sep='\t', encoding='utf-8', dtype={'id': 'str'}, na_values=['NaN']),
                                 args.postgres_users)
            if "relations" in file:
                process_relations_df(cur,
                                     pd.read_csv(os.path.join(args.path, file), sep='\t', encoding='utf-8',
                                                 dtype={'tweet_id': 'str', 'id_source': 'str',
                                                        'id_destination': 'str'}, na_values=['NaN']),
                                     args.postgres_relations)
            if args.remove_processed_files:
                os.remove(os.path.join(args.path, file))
        except Exception as e:
            print(e)

    conn.commit()
    cur.close()
    conn.close()
