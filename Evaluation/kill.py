import sys
import sqlite3
from web3 import Web3, KeepAliveRPCProvider, IPCProvider
import numpy as np
import script
from script import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def get_maxbalance(filename, outfile):
	parselist = open(filename, 'r')
	fp = open(outfile, 'a')
	web3 = Web3(KeepAliveRPCProvider(host='127.0.0.1', port='8666'))
	web31 = Web3(KeepAliveRPCProvider(host='127.0.0.1', port='8545'))
	dbcon = sqlite3.connect('/mnt/d/aashish/db/contract-main.db')
	# dbcon = sqlite3.connect('/Users/ash/contract-db/contract-main.db')
	total_balance = 0
	for instance in parselist:
		instance = instance.split('\n')
		txlist = dbcon.execute("select block from tx where txfrom=? or txto=? and block",(instance[0], instance[0]))
		balance = 0
		max_balance = 0
		max_balance_block = 0
		
		for tran in txlist:
			print "contract: " + instance[0] + ", " + "blocknumber: " + str(tran[0])
			if tran[0] <=4790000:
				balance = max(web3.eth.getBalance(instance[0], int(tran[0])), web3.eth.getBalance(instance[0], int(tran[0])-1))
				if balance>max_balance:
					max_balance = balance
					max_balance_block = tran[0]

			if tran[0] >4790000:
				balance = max(web31.eth.getBalance(instance[0], int(tran[0])), web31.eth.getBalance(instance[0], int(tran[0])-1))
				if balance>max_balance:
					max_balance = balance
					max_balance_block = tran[0]


		total_balance+=max_balance		
		fp.write(instance[0]+'::'+str(max_balance)+'::'+str(max_balance_block)+'\n')

	fp.write('total_balance::'+str(total_balance)+'\n')	
	fp.close()

def get_maxbalanceTP( resultfile, inputfile, outputfile):

	fp = open(resultfile, 'r')
	fp1 = open(inputfile, 'r')
	fp2 = open(outputfile, 'a')
	contract_address = ''
	lines  = fp1.readlines()
	baldict = {}
	tp_balance = 0

	for item in lines:
		items = item.split('::')
		baldict[items[0]] = int(items[1])

	for line in fp:
		array = line.split('::')
		if 'Contract Address' in array[0]:
			contract_address = array[1].split(' ')[1]
			contract_address = contract_address[0:42]

		if 'TP' in line:
			tp_balance += baldict[contract_address]
			fp2.write(contract_address+'::'+str(baldict[contract_address])+'\n')

	fp2.write('True Positive Bal::' + str(tp_balance))		

# get_maxbalance(sys.argv[1], sys.argv[2])
get_maxbalanceTP(sys.argv[1], sys.argv[2], sys.argv[3])

####### Code Complexity graph functions ########

def bugsVssizeHist(filenamekill, n):
	parselistkill = open(filenamekill, 'r')
	web3 = Web3(KeepAliveRPCProvider(host='127.0.0.1', port='8545'))
	dbcon = sqlite3.connect('/mnt/d/aashish/db/contract-main.db')
	sizelistkill = []

	for instance in parselistkill:
		instance = instance.split('\n')
		sizetuple = dbcon.execute("select length(compiled_code),compiled_code from contracts where address="+"'"+instance[0]+"';")
		for item in sizetuple:
			# print item
			sizelistkill.append(int(item[0])/2)		

	sizenumarray3 = np.array(sizelistkill)
	# values, base = np.histogram(sizenumarray1, bins = n)
	# cummulative = np.cumsum(values)
	# # values2, base2 = np.histogram(sizenumarray2, bins = n)
	# # cummulative2 = np.cumsum(values2)
	# values3, base3 = np.histogram(sizenumarray3, bins = n)
	# cummulative3 = np.cumsum(values3)
	# plt.ylabel("bugs")
	# # plt.label("leak vs size distribution")
	# curve1, = plt.plot(base[:-1], cummulative, c='green', label='leak')
	# # curve2, = plt.plot(base2[:-1], cummulative2, c='blue', label='lock')
	# curve3, = plt.plot(base3[:-1], cummulative3, c='red', label='kill')
	# plt.legend(handles=[curve1, curve3], loc=1)
	# # plt.legend(handles=[curve2], loc=2)
	# plt.legend(handles=[curve3], loc=3)

	# plt.savefig("./sizevsbugs.png")

	plt.hist(sizenumarray3, bins = n, color='red', ec='black', lw=2)
	plt.ylabel("number of kill")
	plt.xlabel("bytecode size in bytes")
	plt.savefig('./sizeVsBugsHist/sizevskillHist.png')
	plt.show()		

def bugsVsfunctionsHist(filenamekill, n):
	parselistkill = open(filenamekill, 'r')
	dbcon = sqlite3.connect('/mnt/d/aashish/db/contract-main.db')
	sizelistkill = []
	nfunctions = 0

	for instance in parselistkill:
		instance = instance.split('\n')
		sizetuple = dbcon.execute("select compiled_code from contracts where address="+"'"+instance[0]+"';")
		
		for item in sizetuple:
			complete_disasm = disasm(item[0].split('0x')[1])
			
			for key, value in complete_disasm.iteritems():
				start_point=0
				end_point=len(value[0])
				funclist = funcfind(int(start_point), int(end_point), value[0])
			
			sizelistkill.append(len(funclist))		

	sizenumarray3 = np.array(sizelistkill)

	plt.hist(sizenumarray3, bins = n, color='red', ec='black', lw=2)
	plt.ylabel("number of kill")
	plt.xlabel("number of functions")
	plt.savefig('./functionVsBugsHist/functionvskillHist.png')
	plt.show()			

# bugsVsfunctionsHist(sys.argv[1], 10)
