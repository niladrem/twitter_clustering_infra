CREATE USER twitter WITH PASSWORD 'twitter';
CREATE DATABASE twitter;

GRANT ALL PRIVILEGES ON DATABASE twitter TO twitter;

\c twitter

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO twitter;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO twitter;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO twitter;

CREATE TABLE users (
    id VARCHAR(30) PRIMARY KEY,
    screen_name VARCHAR(50),
    followers_count INTEGER,
    friends_count INTEGER,
    favourites_count INTEGER
);
ALTER TABLE users owner to twitter;

CREATE TABLE relations (
    id SERIAL PRIMARY KEY,
    id_source VARCHAR(30),
    id_destination VARCHAR(30),
    tweet_id VARCHAR(30),
    type VARCHAR(10),
    content TEXT,
    CONSTRAINT fk_id_source
        FOREIGN KEY(id_source)
	    REFERENCES users(id),
	CONSTRAINT fk_id_destination
        FOREIGN KEY(id_destination)
	    REFERENCES users(id)
);

CREATE UNIQUE INDEX simple_relations_idx ON relations (id_source, id_destination, type)
WHERE type IN ('follow', 'friend', 'like');
CREATE UNIQUE INDEX full_relations_idx ON relations (id_source, id_destination, tweet_id, type)
WHERE type NOT IN ('follow', 'friend', 'like');

ALTER TABLE relations owner to twitter;
