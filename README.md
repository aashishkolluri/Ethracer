# Ethracer

This repository contains official Python3 implementation of smart contract analysis tool Ethracer. It can be used to find EO vulnerabilities in smart contracts. For more information about the bugs and the tool, you can read our technical paper *Exploiting the laws of order in smart contracts*.


## Dependencies:
	* Docker.
	* A fully synced Ethereum blockchain runnning over localhost and port 8666.
	* A working network connection between docker and Ethereum blockchain server.


## Steps to run
 
      1. Build docker container from Ethracer directory - sudo docker build -t ethracer .
      2. Run docker - sudo docker run --net='host' -it ethracer bash
      3. Inside container - cd /ethracer/HB && python3.6 main.py --checkone /mnt/c/contracts_solidity/0x325476448021c96c4bf54af304ed502bb7ad0675.sol 0x325476448021c96c4bf54af304ed502bb7ad0675 --blockchain --owner 0x056682f1cf0dc48266c1e47057297a64b58bb6fa
      