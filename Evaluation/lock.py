import sys
import numpy as np
import script
from script import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sqlite3
from web3 import Web3, KeepAliveRPCProvider, IPCProvider

def get_per_n_blocks(file, n, outfile):
	fp1 = open(file, 'r')
	fp = open(outfile, 'a')
	web3 = Web3(KeepAliveRPCProvider(host='127.0.0.1', port='8545'))
	dbcon = sqlite3.connect('/mnt/d/aashish/db/contract-main.db')
	total_balance = 0
	blocklist = []
	blocklist1 = []
	for instance in fp1:
		instance = instance.split('\n')
		blocktuple = dbcon.execute("select block,address from contracts where address="+"'"+instance[0]+"';")
		for item in blocktuple:
			print item
			blocklist1.append(item[0])
	# 	balance = 0
	# 	max_balance = 0
	# 	max_balance_block = 0
		
	# 	for tran in txlist:
	# 		print "contract: " + instance[0] + ", " + "blocknumber: " + str(tran[0])
	# 		balance = max(web3.eth.getBalance(instance[0], int(tran[0])), web3.eth.getBalance(instance[0], int(tran[0])-1))
			
	# 		if balance>max_balance:
	# 			max_balance = balance
	# 			max_balance_block = tran[0]

	# 	total_balance+=max_balance		
	# 	fp.write(instance[0]+'::'+str(max_balance)+'::'+str(max_balance_block)+'\n')

	# sorted_blocklist = blocklist.sort(key=lambda x: x[0])
	# print blocklist
	
	# for item in blocklist:
	# 	print item

	print blocklist1
	# blocknumarray  = np.array([x[0] for y in blocklist for x in y])
	blocknumarray = np.array(blocklist1)
	print blocknumarray
	values, base = np.histogram(blocknumarray, bins = n)
	cummulative = np.cumsum(values)
	plt.plot(base[:-1], cummulative, c='blue')
	plt.savefig("./lock_cum.png")
	plt.show()

	# fp.write('total_balance::'+str(total_balance)+'\n')	
	fp.close()
	fp1.close()




def get_per_n_blocks_hist(file, n, outfile):
	fp1 = open(file, 'r')
	fp = open(outfile, 'a')
	web3 = Web3(KeepAliveRPCProvider(host='127.0.0.1', port='8545'))
	dbcon = sqlite3.connect('/mnt/d/aashish/db/contract-main.db')
	total_balance = 0
	blocklist = []
	blocklist1 = []
	for instance in fp1:
		instance = instance.split('\n')
		blocktuple = dbcon.execute("select block,address from contracts where address="+"'"+instance[0]+"';")
		for item in blocktuple:
			print item
			blocklist1.append(item[0])
	# 	balance = 0
	# 	max_balance = 0
	# 	max_balance_block = 0
		
	# 	for tran in txlist:
	# 		print "contract: " + instance[0] + ", " + "blocknumber: " + str(tran[0])
	# 		balance = max(web3.eth.getBalance(instance[0], int(tran[0])), web3.eth.getBalance(instance[0], int(tran[0])-1))
			
	# 		if balance>max_balance:
	# 			max_balance = balance
	# 			max_balance_block = tran[0]

	# 	total_balance+=max_balance		
	# 	fp.write(instance[0]+'::'+str(max_balance)+'::'+str(max_balance_block)+'\n')

	# sorted_blocklist = blocklist.sort(key=lambda x: x[0])
	# print blocklist
	
	# for item in blocklist:
	# 	print item

	print blocklist1
	# blocknumarray  = np.array([x[0] for y in blocklist for x in y])
	blocknumarray = np.array(blocklist1)
	print blocknumarray
	plt.hist(blocknumarray, normed=True, bins = n)
	plt.savefig("./lock_hist.png")
	plt.show()

	# fp.write('total_balance::'+str(total_balance)+'\n')	
	fp.close()
	fp1.close()

# get_per_n_blocks(sys.argv[1], 100,sys.argv[2])
def get_balances(file, outfile):
	fp1 = open(file, 'r')
	fp = open(outfile, 'a')
	web3 = Web3(KeepAliveRPCProvider(host='127.0.0.1', port='8545'))
	# dbcon = sqlite3.connect('/mnt/d/aashish/contract-main.db')
	total_balance = 0

	for instance in fp1:
		instance = instance.split('\n')
		# blocktuple = dbcon.execute("select block,address from contracts where address="+"'"+instance[0]+"';")
		balance = web3.eth.getBalance(instance[0])
		fp.write(instance[0]+'::'+str(balance)+'\n')
		total_balance += balance

	fp.write("Total Balance::"+ str(total_balance)+'\n')
	fp.close()
	fp1.close()



# get_balances(sys.argv[1], sys.argv[2])
# get_per_n_blocks_hist(sys.argv[1], 50,sys.argv[2])




####### Code Complexity graph functions ########

def bugsVssize(filenamelock, n):
	parselistlock = open(filenamelock, 'r')
	web3 = Web3(KeepAliveRPCProvider(host='127.0.0.1', port='8545'))
	dbcon = sqlite3.connect('/mnt/d/aashish/db/contract-main.db')
	sizelistlock = []

	for instance in parselistlock:
		instance = instance.split('\n')
		sizetuple = dbcon.execute("select length(compiled_code),compiled_code from contracts where address="+"'"+instance[0]+"';")
		for item in sizetuple:
			sizelistlock.append(int(item[0])/2)		

	sizenumarray2 = np.array(sizelistlock)
	# sizenumarray3 = np.array(sizelistkill)
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

	plt.hist(sizenumarray2, bins = n, color='brown', ec='black', lw=2)
	plt.ylabel("number of lock")
	plt.xlabel("bytecode size in bytes")
	# plt.hist(sizenumarray3, bins = n, color='red')
	plt.savefig('./sizeVsBugsHist/sizevslockHist.png')
	plt.show()		

def bugsVsfunctions(filenamelock, n):
	parselistlock = open(filenamelock, 'r')
	web3 = Web3(KeepAliveRPCProvider(host='127.0.0.1', port='8545'))
	dbcon = sqlite3.connect('/mnt/d/aashish/db/contract-main.db')
	sizelistlock = []
	nfunctions = 0

	for instance in parselistlock:
		instance = instance.split('\n')
		sizetuple = dbcon.execute("select compiled_code from contracts where address="+"'"+instance[0]+"';")
		
		for item in sizetuple:
			complete_disasm = disasm(item[0].split('0x')[1])

			for key, value in complete_disasm.iteritems():
				start_point=0
				end_point=len(value[0])
				funclist = funcfind(int(start_point), int(end_point), value[0])
			
			sizelistlock.append(len(funclist))		

	sizenumarray2 = np.array(sizelistlock)
	plt.hist(sizenumarray2, bins = n, color='brown', ec='black', lw=2)
	plt.ylabel("number of lock")
	plt.xlabel("number of functions")
	# plt.hist(sizenumarray3, bins = n, color='red')
	plt.savefig('./functionVsBugsHist/functionvslockHist.png')
	plt.show()

bugsVsfunctions(sys.argv[1], 20)





