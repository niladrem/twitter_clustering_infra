FROM python:3.7-alpine
WORKDIR /code
ENV FLASK_APP=twitter_clustering/app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=development
RUN apk update && \
    apk add --no-cache gcc musl-dev linux-headers git make automake g++ subversion python3-dev
RUN git clone https://github.com/niladrem/twitter_clustering.git && \
    cd twitter_clustering && \
    git checkout origin/gui
COPY . twitter_clustering/
RUN cd twitter_clustering && \
    pip install Cython numpy && \
    pip install -r requirements.txt
EXPOSE 5000
CMD ["flask", "run"]