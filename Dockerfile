# ARG ETHEREUM_VERSION=alltools-v1.8.11
# ARG SOLC_VERSION=0.4.24

FROM ethereum/client-go:alltools-v1.8.11 as geth
FROM ethereum/solc:0.4.24 as solc

FROM ubuntu:16.04

MAINTAINER Aashish Kolluri (aashishkolluri6@gmail.com)

SHELL ["/bin/bash", "-c"]

# Install golang
# RUN apt-get install -y build-essential golang
RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y wget unzip python-virtualenv git build-essential software-properties-common curl
RUN curl -O https://storage.googleapis.com/golang/go1.8.5.linux-amd64.tar.gz && tar -C /usr/local -xzf go1.8.5.linux-amd64.tar.gz && mkdir -p ~/go; \
echo "export GOPATH=$HOME/go" >> ~/.bashrc && echo "export PATH=$PATH:$HOME/go/bin:/usr/local/go/bin" >> ~/.bashrc && source ~/.bashrc

# Install geth and solc
COPY --from=geth /usr/local/bin/evm /usr/local/bin/evm
COPY --from=solc /usr/bin/solc /usr/bin/solc

RUN mkdir /ethracer
COPY . /ethracer/

# RUN mkdir dependencies &&  cd dependencies && wget https://github.com/Z3Prover/z3/archive/master.zip &&  unzip master.zip && cd z3-master &&  python scripts/mk_make.py --prefix=/ --python --pypkgdir=/dependencies && \
# cd build &&  make &&  make install

# ENV PYTHONPATH "${PYTONPATH}:/dependencies"

RUN apt-get install -y python-pip musl-dev pandoc && pip install --upgrade setuptools
RUN pip install requests web3

RUN cd /ethracer/HB && python main.py --checkone /mnt/c/contracts_solidity/0x325476448021c96c4bf54af304ed502bb7ad0675.sol 0x325476448021c96c4bf54af304ed502bb7ad0675 --blockchain

