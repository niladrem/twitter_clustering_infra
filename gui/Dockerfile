FROM python:3.7-buster
WORKDIR /code
RUN apt update -y && \
    apt install -y gcc musl-dev git make automake g++ subversion python3-dev
#ENV LIBRARY_PATH=/lib:/usr/lib
RUN git clone https://github.com/niladrem/twitter_clustering.git && \
    cd twitter_clustering && \
    git checkout origin/gui
COPY . twitter_clustering/
RUN python3 -m pip install --upgrade pip
RUN cd twitter_clustering && \
    pip install Cython numpy Pillow && \
    pip install -r requirements.txt
EXPOSE 5000
ENV FLASK_APP=app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=development
WORKDIR /code/twitter_clustering
CMD ["flask", "run"]