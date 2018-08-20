import os
import re
import glob
import ast
import misc
import sqlite3

contracts = {}
Processed_Contrats_Filename = 'processed_contracts.txt'
Eval_FILE = 'evaluation.txt'
Oyente_FILE = 'result_oyente.txt'
Buggy_Contract_FILE = 'contracts_with_bugs.txt'

def uniquecontracts():
	f = open(Processed_Contrats_Filename, 'r')
	temp_contracts = f.readlines()
	
	for each_line in temp_contracts:
		contract_address = each_line.rstrip('\n')
		if contract_address not in contracts:
			contracts[contract_address] = {}

	print(len(contracts))		

def HB_passed():
	regex = re.compile(r'Process[ 0-9]*:.{3}[a-fA-F0-9]* :.*')
	regex2 = re.compile(r'Total traces  HB passed \/ total :.*')
	f = open(Eval_FILE, 'a')

	for i in range(30):
		Out_filename = 'out'+str(i)+'.txt'
		if os.path.isfile(Out_filename):	 
			fp = open(Out_filename, 'r')
			lines = fp.readlines()
			found1 = False
			contract_address = ''
			for i in range(len(lines)):
				each_line = lines[i]
				match = re.match(regex, each_line.rstrip('\n'))
				if match and not found1:
					contract_address = (each_line.split(' : ')[1]).split(' :')[0]
					found1 = True
					continue

				if found1:
					match1 = re.search(regex2, each_line.rstrip('\n'))
					if match1:
						if not 'hb_passed' in contracts[contract_address]:
							contracts[contract_address]['hb_passed'] = each_line.split('Total traces  HB passed / total :')[1].rstrip('\n')
							
						# f.write(contract_address+' - '+each_line.split('Total traces  HB passed / total :')[1]+'\n')
						continue

				if i < len(lines) - 1: 		
					if '----------------------------------------------------------------------\n'	==  each_line and 'Process' in lines[i+1]:
						found1 = False
						contract_address = ''


def hb_pairs():
	regex = re.compile(r'Process[ 0-9]*:.{3}[a-fA-F0-9]* :.*')
	regex2 = re.compile(r'Simplified HB Relations -----')

	for i in range(30):
		Out_filename = 'out'+str(i)+'.txt'
		if os.path.isfile(Out_filename):	 
			fp = open(Out_filename, 'r')
			lines = fp.readlines()
			found1 = False
			contract_address = ''
			for i in range(len(lines)):
				each_line = lines[i]
				match = re.match(regex, each_line.rstrip('\n'))
				if match and not found1:
					contract_address = (each_line.split(' : ')[1]).split(' :')[0]
					found1 = True
					continue

				if found1:
					match1 = re.search(regex2, each_line.rstrip('\n'))
					if match1:
						if not 'hb_pairs' in contracts[contract_address]:
							contracts[contract_address]['hb_pairs'] = len(eval(lines[i+1].rstrip('\n')))	
							print(contract_address, ' :: ', len(eval(lines[i+1].rstrip('\n')))	)	
						# f.write(contract_address+' - '+each_line.split('Total traces  HB passed / total :')[1]+'\n')
						continue

				if i < len(lines) - 1: 		
					if '----------------------------------------------------------------------\n'	==  each_line and 'Process' in lines[i+1]:
						found1 = False
						contract_address = ''





def nnodes():
	result_files = glob.glob('./reports/*storage-all.txt')

	for each_file in result_files:
		if not os.path.isfile(each_file):  
			print('\033[91m[-] File containing list of nodes %s does NOT exist\033[0m' % args.checkonetrace[0] )
		
		nodes = []
		lines = []
		with open(each_file, 'r') as f:
			lines = f.readlines()

		contract_address = 	(each_file.split('-')[0]).split('/')[-1]
		for line in lines:
			# print(line)	
			if ' : {'	in line:
				# print(line)
				line = re.sub(r'\d{1,3} : \{', '{', line)
				line.rstrip('\n')
				nodes.append(ast.literal_eval(line))

		if 'nnodes' not in contracts[contract_address]:
			contracts[contract_address]['nnodes'] = len(nodes)
			print(contract_address, ' :: ', len(nodes))		

def nfunctions():
	dbcon = sqlite3.connect('/mnt/d/mnt_c/contract-main.db')
	for contract, value in contracts.iteritems():
		c_details = dbcon.execute('select creator, compiled_code from contracts where address='+'"%s"'%(contract))
		owner = ''
		compiled_code = ''
		for each in c_details:
			owner = each[0]
			compiled_code = each[1]

		funclist = misc.get_func_hashes(compiled_code)
		if not 'nfunctions' in value:	
			contracts[contract]['nfunctions'] = len(funclist)
			print(contract, ' :: ', len(funclist))


def notINOyente():
	ucontracts = {}
	ocontracts = {}
	allhbcontracts = {}
	fp1 = open(Buggy_Contract_FILE, 'r')
	filenames = fp1.readlines()
	dbcon = sqlite3.connect('/mnt/c/Happens-Before/HB/eval.db')
	array = dbcon.execute('select address from hbdetails where (mintraces_bal>0 or mintraces_st>0) and id <= 5000')
	array1 = dbcon.execute('select address from hbdetails where id <= 5000')

	for item in array:
		contract_address = item[0]
		if not contract_address in ucontracts:
			ucontracts[contract_address] = 0

	tcontracts = {}		
	for item in array1:
		contract_address = item[0]
		if not contract_address in tcontracts:
			tcontracts[contract_address] = 0

	# for filename in filenames:
	# 	lists = filename.split('/')
	# 	contract_address = ''
	# 	for each in lists:
	# 		if '0x' == each[0:2]:
	# 			contract_address = each.split('-')[0]
	# 			break
		
	# 	if not contract_address in ucontracts:
	# 		ucontracts[contract_address] = 0

	
	fp2 = open(Oyente_FILE, 'r')
	oycontracts = fp2.readlines()
	for each_line in oycontracts:
		elements = each_line.split('::')
		
		if len(elements) >= 2:
			if elements[1] == str(1):
				if not elements[0] in ocontracts:
					# print(elements[0], elements[1])
					ocontracts[elements[0]] = 1


	nOyenteandHB = 0
	nHB = 0

	for key, value in ucontracts.iteritems():
		# print(key)
		if key in ocontracts:
			nOyenteandHB +=1

		else:
			nHB+=1
			ucontracts[key] = 1

	for key, value in ocontracts.iteritems():
		if (not key in ucontracts) and key in contracts:
			print(key) 		
	print(nOyenteandHB, nHB)

	noyente = 0
	for key, value in ocontracts.iteritems():
		if (not key in ucontracts) and key in tcontracts:
			# print(key)
			print(key)
			noyente += 1
	print(noyente)		 


def removeDuplicates(filename, outname):
	f = open(filename, 'r')
	lists = f.readlines()
	fp = open(outname, 'a')
	dbcon = sqlite3.connect('/mnt/d/mnt_c/contract-main.db')
	functionhashes = []

	for line in lists:
		contract_address = (os.path.basename(line.rstrip('\n'))).split('.')[0]

		if '0x'==contract_address[0:2]:
			c_details = dbcon.execute('select creator, compiled_code from contracts where address='+'"%s"'%(contract_address))
			owner = ''
			compiled_code = ''
			for each in c_details:
				owner = each[0]
				compiled_code = each[1]

			funclist = misc.get_func_hashes(compiled_code)
			if not funclist in functionhashes:
				functionhashes.append(funclist)
				fp.write(contract_address+'\n')

def runningTime():

	regex = re.compile(r'Complete running time for contract ')

	for i in range(30):
		Out_filename = 'out'+str(i)+'.txt'
		if os.path.isfile(Out_filename):	 
			fp = open(Out_filename, 'r')
			lines = fp.readlines()
			for line in lines:
				if ('Complete running time for contract ' in line):
					attr = (line.rstrip('\n')).split(', ')	
					contract_address = attr[1]
					time = int(attr[2])
					if not 'runtime' in contracts[contract_address]:
						contracts[contract_address]['runtime'] = time

						print(contract_address, '::',  runtime)






# uniquecontracts()
# HB_passed()	
# hb_pairs()
# nnodes()	
# nfunctions()
notINOyente()
# removeDuplicates()
# runningTime()
