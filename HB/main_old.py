import sqlite3
import argparse
import glob
import os
import math
import multiprocessing
import datetime
from z3 import *
import check_execute
from check_execute import check_one_contract
from values import MyGlobals, initialize_params
import misc
from misc import get_func_hashes, print_function_name, find_blockNumber, getFuncHashes, print_function_name, print_nodes, print_nodes_list
from os import path 
from itertools import product
import sys
import optimize_nodes
from optimize_nodes import *




def exec_main(core_id, core_no, contract_list, read_from_blockchain):



	# DB of passed contracts 
	db_passed_contracts = sqlite3.connect('contracts_checked.db')
	db_passed_contracts.execute('CREATE TABLE IF NOT EXISTS contracts_passed(id INTEGER PRIMARY KEY, address TEXT,bad TEXT, UNIQUE(address) );')
	pc = {}
	for ca in db_passed_contracts.execute('SELECT address,bad from contracts_passed;'):
		pc [ ca[0] ] = ca[1]


	# DB of all contracts
	with open(contract_list, 'r') as cl:
		fp = cl.readlines()

	db_all_contracts = sqlite3.connect('/mnt/d/mnt_c/contract-main.db')
	count = 0

	fp1 = False
	if os.path.isfile('processed_contracts.txt'):
		fp1 = open('processed_contracts.txt', 'r')
		processed_contracts = fp1.readlines()


	for filename in fp:
		filename = filename.rstrip('\n')
		contract_address = os.path.basename(filename).split('.')[0]
		compiled_code = ''
		sol_file = filename

		for item in db_all_contracts.execute('SELECT creator, compiled_code from contracts where address="%s";'%(contract_address)):
			owner = item[0]
			compiled_code = item[1]			

		addr = contract_address 
		code = compiled_code

		if code == '':
			ret = False
			continue
		
		# Parallelization
		count += 1
		if count % int(core_no) != int(core_id): continue


		# If already processed then continue
		if fp1:
			if addr+'\n' in processed_contracts:
				# print('Already processed ', addr,'\n' )
				continue



		# Process the contract
		print('\n'+'-'*70)
		print('Process %7d : %s :%d ' % (count,addr,len(code)) )
		print('-'*70)
		sys.stdout.flush()
		
		# print(sol_file, addr)
		exec_contract(sol_file, addr)


		with open('processed_contracts.txt','a') as f:
			f.write(addr+'\n')
			f.close()
		
		
	print('Finished the whole list !')



debug = False
debug1 = False
read_from_blockchain = True
criteria = 1
nsolutions = 3



def exec_contract(sol_file, c_address):
	dbcon = sqlite3.connect('/mnt/d/mnt_c/contract-main.db')

	if len(c_address) < 1:  print('\033[91m[-] Contract address is incorrect %s \033[0m' % c_address )

	# find the owner and compiled code
	c_details = dbcon.execute('select creator, compiled_code from contracts where address='+'"%s"'%(c_address))
	owner = ''
	compiled_code = ''
	for each in c_details:
		owner = each[0]
		compiled_code = each[1]

	# get the hashes of the functions from the Solidity code
	if not os.path.isfile(sol_file):  
		print('\033[91m[-] Solidity source file %s does NOT exist\033[0m' % sol_file )
		funclist1 = []
	else:
		funclist1 = getFuncHashes(sol_file, debug)

	# Get the hashes of the functions in the specific order as in bytecode.
	funclist = get_func_hashes(compiled_code)
	MyGlobals.functions = copy.deepcopy(funclist)

	# Match bytecode hashes to solidity function names
	funclist2 = []
	for f in funclist:
		fnd = False
		for f1 in funclist1: 
			if f1[1]==f[1]:
				funclist2.append( (f1[0],f1[1]) )
				fnd = True
				break
		if not fnd:
			funclist2.append( (f[1],f[1]) )

	if len(funclist2) == 0:
		print('Something wrong with the contract \n')
		return


	MyGlobals.functions = copy.deepcopy(funclist2)

	# Assuming fallback function is 11111111 (or 22222222 if the previous one is already taken by a legitimate function of the contract)
	found_fallback = False
	for each_pair in funclist2:
		if each_pair == '11111111':
			found_fallback = True
			break
	if found_fallback: funclist2.append(['fallback()', '22222222'])
	else: funclist2.append(['fallback()', '11111111'])

	# find the block at which we want to do analysis if it is not given beforehand
	if not args.atblock:
		MyGlobals.STORAGE_AT_BLOCK = find_blockNumber(c_address)

	# Initialize global parameters
	initialize_params(read_from_blockchain, c_address, nsolutions)
	MyGlobals.max_solutions = nsolutions

	# Append owners to the caller array
	MyGlobals.st['caller'].append(owner.lstrip('0x'))

	print('\nExecuting at blocknumber: \033[92m%d\033[0m'%(MyGlobals.STORAGE_AT_BLOCK))  

	code = compiled_code.replace('\n','').replace('\r','').replace(' ','').lstrip('0x')
	time0 = datetime.datetime.now()

	MyGlobals.Time_checkpoint_HB = datetime.datetime.now()
	# node_list, simplified_hb = check_one_contract( code, c_address, debug, funclist2, read_from_blockchain)
	node_list = [{'tx_value': '0', 'tx_caller': '1111111111111111111111111111111111111111', 'name': 'transfer', 'tx_input': 'a9059cbb0000000000000000000000005fcc7cd3238d87a4cd8efdc93813fece2b5523ce0000000000000000000000000000000000000000000000000000000000000000'}, {'tx_value': '0', 'tx_caller': '767355382fccc2c6e9b4c26ccbaa0398dfb76bbd', 'name': 'Token', 'tx_input': 'c2412676'}, {'tx_value': '0', 'tx_caller': '7777777777777777777777777777777777777777', 'name': 'name', 'tx_input': '06fdde03'}, {'tx_value': '0', 'tx_caller': '7777777777777777777777777777777777777777', 'name': 'symbol', 'tx_input': '95d89b41'}]
	simplified_hb = []	
	
	contract_bytecode = code
	balances =  []
	disasm = op_parse.parse_code(contract_bytecode, debug)
	c_address = hex(int(c_address, 16)).rstrip('L')
	c_address = pad_address(c_address)


	# Find the correct way to give input to the fuzzer.
	# check_all_traces( [], 5, node_list, simplified_hb, [], balances, c_address, contract_bytecode, disasm, debug1, read_from_blockchain )
	print('\nNodes_list_old ',node_list, '\n')
	new_nodes_list, new_simplified_hb = optimize_nodes(node_list, simplified_hb, c_address, disasm, debug, read_from_blockchain, MyGlobals.STORAGE_AT_BLOCK)
	print('\nNodes_list_optimized ',node_list, '\n')
	print('\nNew simplified HB ', new_simplified_hb, '\n')

	for node in new_nodes_list:
		for each in funclist2:
			if node['name'] == each[1]:
				if isinstance(each[0], str):
					node['name'] = each[0]

	print('\nNodes_list_optimized hash replaced',new_nodes_list, '\n')
	print_nodes_list(new_nodes_list)

	# criteria is used to differetiate the buggy traces 0: balances at the end 1: storage at the end
	print('\033[92m\n.....................Now fuzzing between the nodes.....................\n\033[0m')
	time1 = datetime.datetime.now()
	check_all_traces( [], 4, new_nodes_list, new_simplified_hb, [], balances, c_address, contract_bytecode, disasm, criteria, debug1, read_from_blockchain, MyGlobals.STORAGE_AT_BLOCK, time1, False)
	time2 = datetime.datetime.now()

	print('\nTotal time for fuzzing is ', (time2-time1).total_seconds())

	print('\n Complete running time for contract ', c_address, (time2-time0).total_seconds(), '\n\n')


parser = argparse.ArgumentParser()
parser.add_argument("--debug",        help="Print debug info", action='store_true')
parser.add_argument("--debugfuzzer",        help="Print debug info", action='store_true')
parser.add_argument("--printfunc",      type=str,  help="Print function info", action='store', nargs=1)
parser.add_argument("--nsolutions",      type=str,  help="Number of solutions per HB", action='store', nargs=1)
parser.add_argument("--maxTimeHB",      type=str,  help="Maximum time allowed per HB", action='store', nargs=1)
parser.add_argument("--balances",     help="Criteria used in finding buggy traces.", action='store_true')
parser.add_argument("--blockchain",        help="Read storage values from the main blockchain", action='store_true')
parser.add_argument("--atblock",        type=str,   help="Check at certain block number ", action='store', nargs=1)
parser.add_argument("--par",        type=str,   help="Parallel check of contracts from database", action='store', nargs=3)
parser.add_argument("--insert",     help="Insert processed contracts in database", action='store_true')
parser.add_argument("--checkone",        type=str,   help="Check one contract by specifying: 1) the file that holds the bytecode, and, 2) contract's address ", action='store', nargs=2)
parser.add_argument("--fastcheck",        type=str,   help="Check one contract by specifying contract's address", action='store')
args = parser.parse_args()

if args.debug:
	debug = True
if args.debugfuzzer:
	debug1 = True    
if args.printfunc:
	funclist = getFuncHashes(args.printfunc[0], debug) 
	print_function_name(funclist)
if args.nsolutions:
	nsolutions = int(args.nsolutions[0])
if args.maxTimeHB:
	MyGlobals.ONE_HB_TIMEOUT = int(args.maxTimeHB[0])	
if args.balances:
	criteria = 0       
if args.blockchain:
	read_from_blockchain = True
if args.atblock:
	global STORAGE_AT_BLOCK
	MyGlobals.STORAGE_AT_BLOCK = int(args.atblock[0])

if args.par:
	core_id = args.par[0]
	core_no = args.par[1]
	contract_list = args.par[2]
	exec_main(core_id,core_no, contract_list, read_from_blockchain )

# elif args.insert:

#	exec_insert()

elif args.checkone:
	exec_contract(args.checkone[0], args.checkone[1])
	exit(0)

	dbcon = sqlite3.connect('/mnt/d/mnt_c/contract-main.db')

	
