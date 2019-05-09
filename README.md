# Ethracer

This repository contains official Python3 implementation of smart contract analysis tool Ethracer. It can be used to find EO vulnerabilities in smart contracts. For more information about the bugs and the tool, you can read our technical paper [Exploiting the laws of order in smart contracts](https://arxiv.org/abs/1810.11605)


## Dependencies:
	
### Docker
Install docker from [here](https://runnable.com/docker/install-docker-on-linux)

### Ethereum blockchain
Ethracer requires a fully synced blockchain for maximum performance. Sync the blockchain over port 8666, more on this [here](https://github.com/ethereum/go-ethereum). If you have a fully synced blockchain already then,

	 geth --datadir [chainDirectory] --rpc --maxpeers 0 --rpcport 8666

**Important:** There should be a working network connection between docker and Ethereum blockchain server. 


## Steps to run
 
### Build docker container from Ethracer directory 
	sudo docker build -t ethracer .

### Run docker
	sudo docker run --net='host' -it ethracer bash

### Fire Ethracer!
	cd /ethracer/HB && python3.6 main.py --checkone [Contract source code] [Contract address] --blockchain --owner [Owner address]

### Run Tests
Run the command below and check the reports directory. You can find the minimal traces and all the traces with EO bugs for two contracts given in tests folder.

    cd /ethracer && make runTests