import argparse
import glob
import os
import math
import datetime
from z3 import *
import check_execute
from check_execute import WHBFinder
from values import MyGlobals, initialize_params
import misc
from misc import get_func_hashes, print_function_name, find_blockNumber, getFuncHashes, print_function_name, print_nodes, print_nodes_list, print_notimplemented, remove0x
from os import path 
from itertools import product
import sys
import optimize_nodes
from optimize_nodes import *
import global_params
from web3 import Web3


# Initialize global parameters from the file global_params. These values 
# can be overridden by providing inputs using arguments.
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

# Analyze the given contrat for EO bugs.
def exec_contract(sol_file, c_address, owner):
	'''
	First it calls the wHBFinder object to obtain concrete events 
	and wHB relations between them. These events are then fuzzed to 
	find EO bugs.
	'''
	
	debug = MyGlobals.debug
	debug1 = MyGlobals.debug1

	initialize_datastructures()
	
	c_address = Web3.toChecksumAddress(c_address)
	if len(c_address) < 1:  print('\033[91m[-] Contract address is incorrect %s \033[0m' % c_address )

	# find the compiled code from the local blockchain.
	web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8666"))
	compiled_code = web3.eth.getCode(c_address)

	# get the function hashes from the Solidity code
	if not os.path.isfile(sol_file):  
		print('\033[91m[-] Solidity source file %s does NOT exist\033[0m' % sol_file )
		funclist1 = []
	else:
		funclist1 = getFuncHashes(sol_file, debug)

	# Get the function hashes in the specific order as in bytecode.
	compiled_code = str(hex(int.from_bytes(compiled_code, byteorder='big')))
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

	# Initialize remaining private global parameters.
	initialize_params(c_address)

	# Append owners to the caller array which holds possible adddresses of caller field.
	MyGlobals.st['caller'].append(owner.lstrip('0x'))

	print('\nExecuting at blocknumber: \033[92m%d\033[0m'%(MyGlobals.STORAGE_AT_BLOCK))  

	code = compiled_code.replace('\n','').replace('\r','').replace(' ','').lstrip('0x')
	time0 = datetime.datetime.now()
	MyGlobals.Time_checkpoint_HB = datetime.datetime.now()
	c_address = Web3.toChecksumAddress(c_address)
	
	# Delegate static analysis of the bytecode to wHBFinder.
	whbFinderInstance = WHBFinder(code, c_address, debug, funclist2, MyGlobals.read_from_blockchain)
	node_list, simplified_hb = whbFinderInstance.check_one_contract()

	contract_bytecode = code
	balances =  []
	disasm = op_parse.parse_code(contract_bytecode, debug)
	c_address = hex(int(c_address, 16)).rstrip('L')
	c_address = Web3.toChecksumAddress(pad_address(c_address))

	# Find the correct way to give input to the fuzzer.
	new_nodes_list, new_simplified_hb = optimize_nodes(node_list, simplified_hb, c_address, disasm, debug, MyGlobals.read_from_blockchain, MyGlobals.STORAGE_AT_BLOCK)
	for node in new_nodes_list:
		for each in funclist2:
			if node['name'] == each[1]:
				if isinstance(each[0], str):
					node['name'] = each[0]

	print_nodes_list(new_nodes_list)
	print('\nNew simplified HB ', new_simplified_hb, '\n')


	# Pass the events and wHB relations to dynamic analysis component.
	print('\033[92m\n.....................Now fuzzing between the nodes.....................\n\033[0m')
	time1 = datetime.datetime.now()

	# criteria is used to differetiate the buggy traces 0: balances at the end 1: storage at the end
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
parser.add_argument("--checkone",        type=str,   help="Check one contract by specifying: 1) the file that holds the bytecode, and, 2) contract's address ", action='store', nargs=2)
parser.add_argument("--owner",					type=str, help="Provide owner address of the contract", action='store', nargs=1)
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
	MyGlobals.STORAGE_AT_BLOCK = int(args.atblock[0])

if args.checkone:
	if args.owner:
		exec_contract(args.checkone[0], args.checkone[1], args.owner[0])
	else:
		print("Please provide the owner addres\n")
		exit(0)

	exit(0)	