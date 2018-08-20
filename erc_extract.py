from __future__ import print_function
import sqlite3

def extract_erc(start_blocknumber, end_blocknumber, contractlist):

	dbcon = sqlite3.connect('/mnt/c/aashish/db/contract-main.db')
	fp = open(contractlist, 'r')
	
	blocknumber_tuple = []
	for line in fp:
		contract_address = line.rstrip('\n').split('"')[1]
		# print(contract_address)
		contract_details = dbcon.execute('select block, balance from contracts where address='+'"%s"'%(contract_address)+' and block < %d and block > %d'%(end_blocknumber, start_blocknumber))
		
		for item in contract_details:
			# print(item)
			# print('here', item[0], item[1], contract_address)
			blocknumber_tuple.append([[item[0], contract_address], item[1]])
	# print(blocknumber_tuple)
	blocknumber_tuple.sort(key=lambda x: int(x[1]), reverse=True)
		
	for each in blocknumber_tuple:
		print(each[0][1], '%6s'%(':'), each[0][0], each[1])


extract_erc(0, 4800000, 'erc_contracts.txt')			
