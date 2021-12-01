import argparse
import pickle
import pandas as pd
import time
import os

users = []  # id|screen_name|followers_count|friends_count|favourites_count
relations = []  # id_source|id_destination|tweet_id|type|text|query|process_time|created_at


def process_users_dict(users_dict):
    for user_id, user in users_dict.items():
        users.append(tuple([user_id, user.screen_name, user.followers_count, user.friends_count, user.favourites_count]))


def process_relations_dict(relations_dict):
    for relation_type, relation_list in relations_dict.items():
        for rel in relation_list:
            relations.append(tuple([rel['src_user_id'], rel['dst_user_id'], rel['tweet_id'], relation_type, rel['text'],
                                    rel['query'], rel['process_time'], rel['created_at']]))


def parse_args():  # pragma: no cover
    parser = argparse.ArgumentParser()

    parser.add_argument('--input-path', default="/shared/data/raw/")
    parser.add_argument('--output-path', default="/shared/data/formatted/")
    parser.add_argument('--remove-processed-files', type=bool, default=False)

    return parser.parse_args()


def dump_files(args, suffix, usersDf, relationsDf):
    usersDf.to_csv(os.path.join(args.output_path, "users_" + str(int(suffix)) + ".csv"),
                   sep='\t', encoding='utf-8', index=False)

    relationsDf.to_csv(os.path.join(args.output_path, "relations_" + str(int(suffix)) + ".csv"),
                   sep='\t', encoding='utf-8', index=False)


def main_loop(args):
    files = os.listdir(args.input_path)

    for file in files:
        if "users" in file:
            with open(os.path.join(args.input_path, file), "rb") as input_file:
                process_users_dict(pickle.load(input_file))
        if "relations" in file:
            with open(os.path.join(args.input_path, file), "rb") as input_file:
                process_relations_dict(pickle.load(input_file))
        if args.remove_processed_files:
            os.remove(os.path.join(args.input_path, file))


if __name__ == "__main__":
    args = parse_args()

    main_loop(args)

    users = list(set(users))
    relations = list(set(relations))

    usersDf = pd.DataFrame(users, columns=["id", "screen_name", "followers_count", "friends_count", "favourites_count"])
    relationsDf = pd.DataFrame(relations, columns=["id_source", "id_destination", "tweet_id", "type", "text",
                                                   "query", "process_time", "created_at"])

    relationsDf['tweet_id'] = relationsDf['tweet_id'].astype('Int64')

    dump_files(args, time.time(), usersDf, relationsDf)


