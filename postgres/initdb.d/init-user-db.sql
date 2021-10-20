CREATE USER twitter WITH PASSWORD 'twitter';
CREATE DATABASE twitter;

GRANT ALL PRIVILEGES ON DATABASE twitter TO twitter;

\c twitter

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO twitter;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO twitter;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO twitter;

CREATE TABLE tweet (
id serial,
content text
);

ALTER TABLE tweet owner to twitter;