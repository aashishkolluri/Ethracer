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
	web3 = Web3(KeepAliveRPCProvider(host='127.0.0.1', port='8545'))
	dbcon = sqlite3.connect('/mnt/d/aashish/db/contract-main.db')
	# dbcon = sqlite3.connect('/Users/ash/contract-db/contract-main.db')
	total_balance = 0
	for instance in parselist:
		instance = instance.split('\n')
		txlist = dbcon.execute("select block from tx where txfrom=? or txto=? and block > 4500000",(instance[0], instance[0]))
		balance = 0
		max_balance = 0
		max_balance_block = 0
		
		for tran in txlist:
			print "contract: " + instance[0] + ", " + "blocknumber: " + str(tran[0])
			balance = max(web3.eth.getBalance(instance[0], int(tran[0])), web3.eth.getBalance(instance[0], int(tran[0])-1))
			if balance>max_balance:
				max_balance = balance
				max_balance_block = tran[0]

		total_balance+=max_balance		
		fp.write(instance[0]+'::'+str(max_balance)+'::'+str(max_balance_block)+'\n')

	fp.write('total_balance::'+str(total_balance)+'\n')	
	fp.close()

# get_maxbalance(sys.argv[1], sys.argv[2])



####### Code Complexity graph functions ########

def bugsVssize(filenameleak, n):
	parselist = open(filenameleak, 'r')
	web3 = Web3(KeepAliveRPCProvider(host='127.0.0.1', port='8545'))
	dbcon = sqlite3.connect('/mnt/d/aashish/db/contract-main.db')
	sizelist = []

	for instance in parselist:
		instance = instance.split('\n')
		sizetuple = dbcon.execute("select length(compiled_code),compiled_code from contracts where address="+"'"+instance[0]+"';")
		for item in sizetuple:
			# print item
			sizelist.append(int(item[0])/2)

	sizenumarray1 = np.array(sizelist)
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

	plt.hist(sizenumarray1, bins = n, color='green', ec='black', lw=2)
	plt.ylabel("number of leak")
	plt.xlabel("bytecode size in bytes")
	plt.savefig('./sizeVsBugsHist/sizevsleakHist.png')
	plt.show()	

def bugsVsfunctions(filenameleak, n):
	parselist = open(filenameleak, 'r')
	web3 = Web3(KeepAliveRPCProvider(host='127.0.0.1', port='8545'))
	dbcon = sqlite3.connect('/mnt/d/aashish/db/contract-main.db')
	sizelistleak = []
	nfunctions = 0

	for instance in parselist:
		instance = instance.split('\n')
		sizetuple = dbcon.execute("select compiled_code from contracts where address="+"'"+instance[0]+"';")
		
		for item in sizetuple:
			complete_disasm = disasm(item[0].split('0x')[1])
			
			for key, value in complete_disasm.iteritems():
				start_point=0
				end_point=len(value[0])
				funclist = funcfind(int(start_point), int(end_point), value[0])
			
			sizelistleak.append(len(funclist))

	sizenumarray1 = np.array(sizelistleak)
	plt.hist(sizenumarray1, bins = n, color='green', ec='black', lw=2)
	plt.ylabel("number of leak")
	plt.xlabel("number of functions")
	plt.savefig('./functionVsBugsHist/functionvsleakHist.png')
	plt.show()				

bugsVsfunctions(sys.argv[1],10)

