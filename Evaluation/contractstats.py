import sqlite3
import math
import script
from script import *
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import *

def baldist():

	listbal = []
	dbcon = sqlite3.connect('/mnt/d/aashish/db/contract-main.db')
	balances = dbcon.execute("select balance from contracts")

	for item in balances:
		listbal.append(item[0])

	listbal.sort()
	xlist = [x for x in range(1,101)]
	ylist = []
	sumbal = 0
	
	for i in range(len(listbal)):
		sumbal += listbal[i] 
		if (i+1)%9709==0 or i==970897 :
			ylist.append(math.log10(sumbal+1))
			sumbal=0

	print xlist, ylist

	xlist1 = [float(x)/10 for x in range(970,1000)]
	ylist1 = []
	sumbal1 = 0
	i=0

	for i in range(len(listbal)):
		sumbal1 += listbal[i] 
		if (i+1)%971==0 and i>=970*971 or i==970897 :
			ylist1.append(math.log10(sumbal1+1))
			sumbal1=0

	print xlist1, ylist1
	fig, axs = plt.subplots(1, 2, sharey=True, tight_layout=True)
	print axs[0], axs[1]
	axs[0].plot(xlist, ylist, c='blue')
	axs[1].plot(xlist1, ylist1, c='blue')
	axs[0].set_xlabel('Percentile of contracts w.r.t balances')
	axs[0].set_ylabel('sum of balances of every percentile in log base 10')
	axs[1].set_label('magnified')
	
	# plt.xticks(xlist)
	plt.savefig("./contractstats/baldistnomag.png")

def baldistmag():

	listbal = []
	dbcon = sqlite3.connect('/mnt/d/aashish/db/contract-main.db')
	balances = dbcon.execute("select balance from contracts")

	for item in balances:
		listbal.append(item[0])

	listbal.sort()
	xlist1 = [float(x)/10 for x in range(970,1000)]
	ylist1 = []
	sumbal1 = 0
	i=0

	for i in range(len(listbal)):
		sumbal1 += listbal[i] 
		if (i+1)%971==0 and i>=970*971 or i==970897 :
			ylist1.append(math.log10(sumbal+1))
			sumbal1=0

	print xlist1, ylist1
	plt.plot(xlist1, ylist1, c='blue')
	# plt.xticks(xlist)
	plt.savefig("./contractstats/baldist.png")


def sizedist():

	listsize = []
	dbcon = sqlite3.connect('/mnt/d/aashish/db/contract-main.db')
	sizes = dbcon.execute("select length(compiled_code)/2 from contracts")

	for item in sizes:
		listsize.append(item[0])

	plt.hist(np.array(listsize), bins = 10, log=True, color='grey', ec='black', lw=2)
	plt.ylabel('number of contracts')
	plt.xlabel('size in bytes')
	plt.savefig('./contractstats/sizedisthistlog.png')

def funcdist():

	dbcon = sqlite3.connect('/mnt/d/aashish/db/contract-main.db')
	funclist = []
	codelist = []
	codes = dbcon.execute('select address, compiled_code from contracts')
	
	for item in codes:
		codelist.append([item[0], item[1]])

	for tuples in codelist:
		complete_disasm = disasm(tuples[1].split('0x')[1])

		for key, value in complete_disasm.iteritems():
				start_point=0
				end_point=len(value[0])
				funclist.append(len(funcfind(int(start_point), int(end_point), value[0])))

	print funclist[0:100]
	funcnumarray = np.array(funclist)
	plt.hist(funcnumarray, bins = 20, log=True, color='lightgrey', ec='black', lw=2)
	plt.ylabel("number of contracts")
	plt.xlabel("number of functions")
	# plt.hist(sizenumarray3, bins = n, color='red')
	plt.savefig('./contractstats/funcdistlog.png')
	plt.show()	

def transactionVsbalance():
	
	dbcon = sqlite3.connect('/mnt/d/aashish/db/contract-main.db')
	transactionarray = dbcon.execute('select balance, address from contracts')
	transactionlist = []
	
	for item in transactionarray:
		# print item[0], item[1]
		transactionlist.append([item[0], item[1]])

	txcount = []

	for each in transactionlist:
		txarray = dbcon.execute('select count(txhash) from tx where txfrom='+'"'+each[1]+'"'+ ' or txto='+'"'+each[1]+'"')
		for num in txarray:
			if num[0] < 1500:
				txcount.append([each[0], num[0]])

	txcount.sort(key=lambda x: int(x[1]))
	ylist = []
	xlist = []
	
	for items in txcount:
		print items[0], items[1]
		ylist.append(items[0])
		xlist.append(items[1])

	plt.plot(xlist,ylist, c='red')
	plt.savefig('./contractstats/transactiondistmoremag.png')


def timeDist(n):
	dbcon = sqlite3.connect('/mnt/c/Happens-Before/HB/eval.db')
	timearray = dbcon.execute('select runtime from hbdetails order by runtime')
	timelist = []
	for item in timearray:
		timelist.append(item[0])

	plt.hist(timelist, bins=n, color='lightgrey', ec='black', lw=2)
	plt.xlabel('Runtime')
	plt.ylabel('Number of contracts')

	plt.savefig('./contractstats/timeDist.png')




# sizedist()
# funcdist()
# transactionVsbalance()
timeDist(20)