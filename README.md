# twitter_clustering_infra

## How to run
`docker build -t processing_module processing_module/`

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

### Tests & coverage
`coverage run -m unittest discover processing_module/tests`

`coverage report -m`