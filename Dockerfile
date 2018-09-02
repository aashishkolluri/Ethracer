FROM ethereum/client-go:alltools-v1.8.11 as geth
FROM ethereum/solc:0.4.24 as solc

FROM ubuntu:16.04

MAINTAINER Aashish Kolluri (aashishkolluri6@gmail.com)

SHELL ["/bin/bash", "-c", "-l"]

# Install golang
# RUN apt-get install -y build-essential golang
RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y software-properties-common python-software-properties

RUN add-apt-repository ppa:jonathonf/python-3.6
RUN apt-get update
RUN apt-get install -y build-essential python3.6 python3.6-dev python3-pip python3.6-venv

RUN apt-get install -y wget unzip python-virtualenv git build-essential software-properties-common curl
RUN curl -O https://storage.googleapis.com/golang/go1.8.5.linux-amd64.tar.gz && tar -C /usr/local -xzf go1.8.5.linux-amd64.tar.gz && mkdir -p ~/go; \
echo "export GOPATH=$HOME/go" >> ~/.bashrc && echo "export PATH=$PATH:$HOME/go/bin:/usr/local/go/bin" >> ~/.bashrc && source ~/.bashrc

# Install geth and solc
COPY --from=geth /usr/local/bin/evm /usr/local/bin/evm
COPY --from=solc /usr/bin/solc /usr/bin/solc

RUN mkdir /ethracer
COPY . /ethracer/

RUN mkdir dependencies 
RUN cd dependencies && wget https://github.com/Z3Prover/z3/archive/master.zip &&  unzip master.zip && cd z3-master &&  python3.6 scripts/mk_make.py --prefix=/ --python --pypkgdir=/dependencies && \
cd build &&  make &&  make install

ENV PYTHONPATH "${PYTONPATH}:/dependencies"

RUN apt-get install -y python-pip python3-pip musl-dev pandoc && pip3 install --upgrade setuptools
RUN python3.6 -m pip install requests web3 pysha3
EXPOSE 80


#RUN cd /ethracer/HB && python3.6 main.py --checkone /mnt/c/contracts_solidity/0x325476448021c96c4bf54af304ed502bb7ad0675.sol 0x325476448021c96c4bf54af304ed502bb7ad0675 --blockchain --owner 0x056682f1cf0dc48266c1e47057297a64b58bb6fa
# have to configure IP tables with ---> iptables -A INPUT -i docker0 -j ACCEPT; and then start docker with ---> sudo docker run --net='host' -it ethracer; 
#sudo docker build -t ethracer  && sudo docker run --net='host' -it ethracer bash