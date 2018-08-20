import sqlite3
from web3 import Web3, KeepAliveRPCProvider, IPCProvider

def add_balance_and_kill():
	dbcon = sqlite3.connect('/mnt/d/aashish/db/contract-main.db')
	dbcon.execute("alter table contracts add column killblock INT default 0")
	dbcon.execute("alter table contracts add column balance BIGINT default 0")


def update_balance_and_kill():
	dbcon = sqlite3.connect('/mnt/d/aashish/db/contract-main.db')
	c = dbcon.cursor()
	c.execute('SELECT * FROM contracts')
	web3 = Web3(KeepAliveRPCProvider(host='127.0.0.1', port='8545'))
	d = dbcon.cursor()
	
	for row in c:
		if int(row[0])<960000:
			continue
		code = web3.eth.getCode(row[1])
		
		if code =='0x':
			d.execute('update contracts set killblock=1 where address='+'"'+row[1]+'"')

		balance = web3.eth.getBalance(row[1])
		# print balance
		d.execute('update contracts set balance='+str(balance)+' where address='+'"'+row[1]+'"')
		if int(row[0])%2000==0 or int(row[0])%970898==0:
			print row[0], " :: ", row[1]
		if int(row[0])%970898==0:
			dbcon.commit()

# def posthumous():
# 	dbcon = sqlite3.connect('/mnt/d/aashish/db/contract-main.db')
# 	c = dbcon.cursor()
# 	c.execute('SELECT * FROM contracts')
# 	web3 = Web3(KeepAliveRPCProvider(host='127.0.0.1', port='8545'))
# 	d = dbcon.cursor()

# 	for row in c:
		


update_balance_and_kill()