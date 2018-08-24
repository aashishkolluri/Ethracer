import sqlite3
import argparse
import glob
import os
import math
import multiprocessing
import datetime
from z3 import *
import check_execute
from check_execute import WHBFinder
from values import MyGlobals, initialize_params
import misc
from misc import get_func_hashes, print_function_name, find_blockNumber, getFuncHashes, print_function_name, print_nodes, print_nodes_list, print_notimplemented
from os import path 
from itertools import product
import sys
import re
import ast
import optimize_nodes
from optimize_nodes import *
import global_params



# Called when contracts are executed in parallel, on differet cores.

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

	processed_contracts = []
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
		if addr+'\n' in processed_contracts:
			# print('Already processed ', addr,'\n' )
			continue



		# Process the contract
		print('\n'+'-'*70)
		print('Process %7d : %s :%d ' % (count,addr,len(code)) )
		print('-'*70)
		sys.stdout.flush()

		with open('processed_contracts.txt','a') as f:
			f.write(addr+'\n')
			f.close()

		# Start analysing the contract.
		exec_contract(sol_file, addr)


		


def initParams():
	MyGlobals.debug = False
	MyGlobals.debug1 = False
	MyGlobals.max_solutions = global_params.MAX_SOLUTIONS
	MyGlobals.read_from_blockchain = global_params.READ_FROM_BLOCKCHAIN

	try:
		MyGlobals.STORAGE_AT_BLOCK = global_params.STORAGE_AT_BLOCK
	except AttributeError:
		pass
	try:
		MyGlobals.MAX_JUMP_DEPTH = global_params.MAX_JUMP_DEPTH
	except AttributeError:
		pass
	try:
		MyGlobals.MAX_VISITED_NODES = global_params.MAX_VISITED_NODES
	except AttributeError:
		pass
	try:
		MyGlobals.SOLVER_TIMEOUT = global_params.SOLVER_TIMEOUT
	except AttributeError:
		pass
	try:
		MyGlobals.ONE_CONTRACT_HB_TIMEOUT = global_params.ONE_CONTRACT_HB_TIMEOUT
	except AttributeError:
		pass
	try:
		MyGlobals.ONE_HB_TIMEOUT = global_params.ONE_HB_TIMEOUT
	except AttributeError:
		pass		


# Initialize all datastructures which are required for analysis.
def initialize_datastructures():
	MyGlobals.functions[:] = []
	MyGlobals.symbolic_vars[:] = []
	MyGlobals.function_calls.clear()
	MyGlobals.datastructures.clear()
	MyGlobals.funcvardata.clear()
	MyGlobals.sha3vardata.clear()
	MyGlobals.solution_dict.clear()

# This is the entry point to actual analysis of a cotract. This function initializes all the necessary information to do the analysis.
def exec_contract(sol_file, c_address):
	debug = MyGlobals.debug
	debug1 = MyGlobals.debug1

	initialize_datastructures()
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

	# Initialize remaining private global parameters.
	initialize_params(c_address)

	# Append owners to the caller array
	MyGlobals.st['caller'].append(owner.lstrip('0x'))

	print('\nExecuting at blocknumber: \033[92m%d\033[0m'%(MyGlobals.STORAGE_AT_BLOCK))  

	code = compiled_code.replace('\n','').replace('\r','').replace(' ','').lstrip('0x')
	time0 = datetime.datetime.now()

	MyGlobals.Time_checkpoint_HB = datetime.datetime.now()
	whbFinderInstance = WHBFinder(code, c_address, debug, funclist2, MyGlobals.read_from_blockchain)
	node_list, simplified_hb = whbFinderInstance.check_one_contract()
	# node_list = [{'tx_caller': 'cee827be9b520a485db84d1f09cc0a99ea878686', 'name': '095ea7b3', 'tx_blocknumber': '493e00', 'tx_value': '0', 'tx_timestamp': '5a5c001d', 'tx_input': '095ea7b3000000000000000000000000cee827be9b520a485db84d1f09cc0a99ea8786860000000000000000000000000000000000000000000000000000000001457000'}, {'tx_caller': 'cee827be9b520a485db84d1f09cc0a99ea878686', 'name': '23b872dd', 'tx_blocknumber': '493e00', 'tx_value': '0', 'tx_timestamp': '5a5c001d', 'tx_input': '23b872dd000000000000000000000000cee827be9b520a485db84d1f09cc0a99ea87868600000000000000000000000018a230ec24cab7bf27b001f712ab1480ad979c3a0000000000000000000000000000000000000000000000000000000001457000'}, {'tx_caller': 'cee827be9b520a485db84d1f09cc0a99ea878686', 'name': '23b872dd', 'tx_blocknumber': '493e00', 'tx_value': '0', 'tx_timestamp': '5a5c001d', 'tx_input': '23b872dd000000000000000000000000cee827be9b520a485db84d1f09cc0a99ea878686000000000000000000000000cee827be9b520a485db84d1f09cc0a99ea8786860000000000000000000000000000000000000000000000000000000001457000'}, {'tx_value': '0', 'tx_caller': 'cee827be9b520a485db84d1f09cc0a99ea878686', 'name': 'a9059cbb', 'tx_input': 'a9059cbb00000000000000000000000003eedb3109c1bec4598c5e0353daa2661b2d46e90000000000000000000000000000000000000000000000000000000000000100'}]
	# simplified_hb = [(0, 1), (0, 2)]	
	
	contract_bytecode = code
	balances =  []
	disasm = op_parse.parse_code(contract_bytecode, debug)
	c_address = hex(int(c_address, 16)).rstrip('L')
	c_address = pad_address(c_address)


	# Find the correct way to give input to the fuzzer.
	# check_all_traces( [], 5, node_list, simplified_hb, [], balances, c_address, contract_bytecode, disasm, debug1, read_from_blockchain )
	print('\nNodes_list_old ',node_list, '\n')
	new_nodes_list, new_simplified_hb = optimize_nodes(node_list, simplified_hb, c_address, disasm, debug, MyGlobals.read_from_blockchain, MyGlobals.STORAGE_AT_BLOCK)
	print('\nNodes_list_optimized ',new_nodes_list, '\n')
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

	if not args.balances: 
		criteria = global_params.CHECK_FOR_BALANCE

	check_all_traces( [], 4, new_nodes_list, new_simplified_hb, [], balances, c_address, contract_bytecode, disasm, criteria, debug1, MyGlobals.read_from_blockchain, MyGlobals.STORAGE_AT_BLOCK, time1, False)
	time2 = datetime.datetime.now()

	print('Printing not implemented ins for contract %s'%(c_address))
	print_notimplemented()
	MyGlobals.notimplemented_ins.clear()
	print('Done printing not implemented ins')

	print('\nTotal time for fuzzing is ', (time2-time1).total_seconds())

	print('\n Complete running time for contract ', c_address, (time2-time0).total_seconds(), '\n\n')


# Execute only one trace (used for debugging purposes)
def check_trace(nodes, c_address, trace):
	dbcon = sqlite3.connect('/mnt/d/mnt_c/contract-main.db')

	if len(c_address) < 1:  print('\033[91m[-] Contract address is incorrect %s \033[0m' % c_address )

	# find the owner and compiled code
	c_details = dbcon.execute('select creator, compiled_code from contracts where address='+'"%s"'%(c_address))
	owner = ''
	compiled_code = ''
	for each in c_details:
		owner = each[0]
		compiled_code = each[1]

	if not args.atblock:
		MyGlobals.STORAGE_AT_BLOCK = find_blockNumber(c_address)
			
	code = compiled_code.replace('\n','').replace('\r','').replace(' ','').lstrip('0x')	

	contract_bytecode = code
	balances =  []
	disasm = op_parse.parse_code(contract_bytecode, MyGlobals.debug)
	c_address = hex(int(c_address, 16)).rstrip('L')
	c_address = pad_address(c_address)

	preprocess(c_address, trace, nodes)
	strtrace = ''
	fulltrace = []
	for each_index in trace:
		fulltrace.append(nodes[each_index])
		strtrace+=str(each_index)+'	'
	storage = {}
	# temp_storage.clear()
	print('\033[94m Executing the trace: %s\033[0m\n'%(strtrace))
	ct = check_one_trace(c_address, fulltrace, storage, disasm, True, True, MyGlobals.STORAGE_AT_BLOCK)
	print('Storage: \n', storage)
	if ct:
		print('\033[92m[+]Executed trace: %s\033[0m\n'%(strtrace))



# initializeGlobalParams
initParams()


# Argument parser

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
parser.add_argument("--checkonetrace",			type=str, help="Check a trace by executing it", action='store', nargs=3)
args = parser.parse_args()

if args.debug:
	MyGlobals.debug = True
if args.debugfuzzer:
	MyGlobals.debug1 = True    
if args.printfunc:
	funclist = getFuncHashes(args.printfunc[0], MyGlobals.debug) 
	print_function_name(funclist)
if args.nsolutions:
	MyGlobals.max_solutions = int(args.nsolutions[0])
if args.maxTimeHB:
	MyGlobals.ONE_HB_TIMEOUT = int(args.maxTimeHB[0])	
if args.balances:
	MyGlobals.criteria = 0       
if args.blockchain:
	MyGlobals.read_from_blockchain = True
if args.atblock:
	global STORAGE_AT_BLOCK
	MyGlobals.STORAGE_AT_BLOCK = int(args.atblock[0])

if args.par:
	core_id = args.par[0]
	core_no = args.par[1]
	contract_list = args.par[2]
	exec_main(core_id,core_no, contract_list, MyGlobals.read_from_blockchain )

# elif args.insert:

#	exec_insert()

elif args.checkone:
	exec_contract(args.checkone[0], args.checkone[1])
	exit(0)

	dbcon = sqlite3.connect('/mnt/d/mnt_c/contract-main.db')

elif args.checkonetrace:
	if not os.path.isfile(args.checkonetrace[0]):  
		print('\033[91m[-] File containing list of nodes %s does NOT exist\033[0m' % args.checkonetrace[0] )
	
	nodes = []
	lines = []
	with open(args.checkonetrace[0], 'r') as f:
		lines = f.readlines()

	for line in lines:
		# print(line)	
		if ' : {'	in line:
			# print(line)
			line = re.sub(r'\d{1,3} : \{', '{', line)
			line.rstrip('\n')
			nodes.append(ast.literal_eval(line))


	trace = args.checkonetrace[2].split('-')
	for i in range(0, len(trace)):
		trace[i] = int(trace[i])

	# print(nodes, trace)	
	# exit(0)	
	check_trace(nodes, args.checkonetrace[1], trace)	

	
	