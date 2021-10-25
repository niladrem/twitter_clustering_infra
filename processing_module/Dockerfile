FROM rundeck/rundeck:3.4.3

USER root

RUN apt-get -qq update && apt-get -qq -y install curl bzip2 \
    && curl -sSL https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -o /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -bfp /usr/local \
    && rm -rf /tmp/miniconda.sh \
    && conda install -y python=3 \
    && conda update conda \
    && apt-get -qq -y remove curl bzip2 \
    && apt-get -qq -y autoremove \
    && apt-get autoclean \
    && rm -rf /var/lib/apt/lists/* /var/log/dpkg.log \
    && conda clean --all --yes

COPY requirements.txt .

RUN conda create -n twitter -y  && \
    conda init && \
    . /home/rundeck/.bashrc && \
    . /usr/local/etc/profile.d/conda.sh && \
    conda activate twitter && \
    pip install -r requirements.txt

ENV PATH /opt/conda/bin:$PATH
