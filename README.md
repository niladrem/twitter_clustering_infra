# twitter_clustering_infra

## How to run
`docker-compose up`

`docker-compose rm -f` - remove stopped containers

User:
- login: twitter
- password: twitter
- database: twitter

## Access to rundeck
- url: localhost:4440
- login: admin
- password: admin

## Access to clustering
localhost:5000

### Tests & coverage
`coverage run -m unittest discover processing_module/tests`

`coverage report -m`