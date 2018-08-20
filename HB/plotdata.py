from __future__ import print_function
from web3 import Web3, KeepAliveRPCProvider, IPCProvider
import sqlite3
import matplotlib.pyplot as plt





# Find max Ether
fname = 'plotsuicide.txt'
with open(fname,'r') as f:
	l = f.readlines()

pc = {}
for cl in l:
	cl = cl.replace('\n','')
	pc[cl] = True

#print(pc)

web3 = Web3(KeepAliveRPCProvider(host='127.0.0.1', port='8545'))
lastblock = web3.eth.blockNumber

db = sqlite3.connect('../contract-main.db')
for c in pc:

	# Find creation block 
	sblock = 0
	for ca in db.execute('SELECT block from contracts where address = "'+c+'";'):
		sblock = ca[0]

	print('%d %d ' % (sblock,lastblock))

	maxbal = 0
	for r in (sblock,lastblock):
		balance = web3.eth.getBalance(c,r)
		if balance > maxbal:
			maxbal = balance

	print(c)
	print(maxbal)



	continue

	balance = web3.eth.getBalance(c)
	eth = float(balance)/ (10**18)
	if  eth >= 0.0001:
		print(eth)





#print(pc)
exit(0)




pc = {}

with open('plotsuicide.txt','r') as f:
#with open('plotcontract.txt','r') as f:
	l = f.readlines()







BREAKS = 10000
total_contracts = []
weake_contracts = []
vals = []
count = 0
found = 0
total_count = 0
weake_count = 0
db = sqlite3.connect('../contract-main.db')
for ca in db.execute('SELECT address from contracts order by block asc;'):
	total_count += 1
	if ca[0] in pc:
		weake_count += 1
		found += 1
	count += 1
	if count == BREAKS:
		total_contracts.append(count)
		weake_contracts.append(found)
		count = 0
		found = 0

if count > 0:
	total_contracts.append(count)
	weake_contracts.append(found)

for i in range(len(total_contracts)):
	print('%6d / %6d' % (weake_contracts[i], total_contracts[i]))
print('Number of contracts: %d' % total_count)
print('Buggy     contracts: %d' % weake_count)


t = range(len(total_contracts))
n = [ float(weake_contracts[i])/ total_contracts[i] / 10000 for i in range(len(total_contracts)) ]


start  = 10

print(n)


plt.plot(t[start:],n[start:])
plt.show()
