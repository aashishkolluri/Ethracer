from __future__ import print_function
import sqlite3

def extract_erc(start_blocknumber, end_blocknumber, contractlist):

	dbcon = sqlite3.connect('/mnt/Ash_ssd/db/contract-main.db')
	fp = open(contractlist, 'r')

	for line in fp:
		contract_address = line.rstrip('\n').split('"')[1]
		contract_details = dbcon.execute('select block, balance from contracts where block < %d and block > %d'%(end_blocknumber, start_blocknumber))
		blocknumber_tuple = []

		for item in contract_details:
			blocknumber_tuple.append([item[0], item[1]])

		blocknumber_tuple.sort(key=lambda x: int(x[0]), reverse=True)
		
		for each in blocknumber_tuple:
			print(each[0], '%6s'%(':'), each[1])


extract_erc(0, 480000, 'erc_contracts.txt')			