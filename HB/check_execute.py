from __future__ import print_function
from parse_code import *
import copy
from values import get_params, set_params, initialize_params, print_params, MyGlobals, clear_globals, optimize_hb
from execute_block import * 
from cfg import *
import z3 
from z3 import *
import datetime
from os import path 
import sys
sys.path.insert(0, '../fuzzer')

from check import *
import op_parse

# from op_parse import parse_code
from search_enhance import stateChangingFunctions

def changeContext(key, value, debug = False):
	# if debug: 
	print ('%-20s :  %s ' % (key, str(value)) )
	if not ('input' in key and not 'inputlength' in key):
		if isinstance(value, str):
			value = int(value, 16)
		
		else:		
			value = int(value.as_long())

	if 'input' in key and not 'inputlength' in key:
		key = 'tx_input'
	
	if 'CALLVALUE' in key:
		if value > 10**19:
			value = 10**19
		key = 'tx_value'

	if 'NUMBER' in key:
		if value > 4800000:
			value = 4800000
		key = 'tx_blocknumber'

	if 'GASLIMIT' in key:

		key = 'tx_gaslimit'

	if 'TIMESTAMP' in key:
		if value > 1515978781:
			value = 1515978781
		key = 'tx_timestamp'

	if 'ADDRESS' in key:
		value = ((hex(value).ljust(40, '0')).rstrip('L')).lstrip('0x')
		key = 'contract_address'

	if 'ORIGIN' in key:
		value = ((hex(value).ljust(40, '0')).rstrip('L')).lstrip('0x')
		key = 'tx_origin'

	if 'BLOCKHASH' in key:
		key = 'tx_blockhash'
	
	if 'BALANCE' in key:
		if value > 10000:
			value = 10000	
		key = 'contract_balance'

	if 'CALLER' in key:
		if not (hex(value).rstrip('L').lstrip('0x') in MyGlobals.st['caller']) and not (len(hex(value).rstrip('L').lstrip('0x')) == 40 and not (hex(value).rstrip('L').lstrip('0x') == 'ffffffffffffffffffffffffffffffffffffffff')):
			value = '7'*40
		else:
			value = (hex(value).rstrip('L')).lstrip('0x')

		key = 'tx_caller'

	if not ('input' in key and not 'inputlength' in key):	
		if not isinstance(value, str) and (not value ==0):	
			value = hex(value).rstrip('L').lstrip('0x')

		if value ==0:
			value = '0'	

	return key, value





def check_one_contract(contract_bytecode, contract_address, debug, funclist, read_from_blockchain, par = False, que = None):

	a = datetime.datetime.now()

	if len(contract_bytecode) <= 2:
		print('Contract bytecode is too short:\n\tlen:%d\n\tbytecode:%s' % (len(contract_bytecode), contract_bytecode) )
		return False



	solution_dict = {}
	func_hash = {}
	for f in funclist:
		func_hash[f[1]]= f[0]

	print('Found functions:  \033[92m %d \033[0m\n' % len(funclist))
	impFunctionList, function_pairs_list  = stateChangingFunctions(funclist, contract_bytecode, contract_address, read_from_blockchain, debug)
	t2 = datetime.datetime.now()
	if MyGlobals.ONE_CONTRACT_HB_TIMEOUT < int((t2 - MyGlobals.Time_checkpoint_HB).total_seconds()):
		print('\n', '\033[91m-------Finding the HB relations timed out\033[0m', '\n')
		return [], []	
	print('Important functions: \033[92m%3d  out of  %d  \033[0m' % (len(impFunctionList), len(funclist)) )
	for f in impFunctionList:
		print('%10s : %s' % (f, func_hash[f] if f in func_hash else f))
	print('Function HB pairs:  \033[92m %d  \033[0m' % len(function_pairs_list))
	for fp in function_pairs_list:
		print('%10s , %10s  :  %s  , %s' % (fp[0],fp[1], func_hash[fp[0]] if fp[0] in func_hash else fp[0], func_hash[fp[1]] if fp[1] in func_hash else fp[1]))

	cnt = 0
	for pair in function_pairs_list:
		if pair[0]!=pair[1]:
			MyGlobals.Time_checkpoint = datetime.datetime.now()
			MyGlobals.ONE_HB_TIMEOUT = 2*60
			MyGlobals.num_solver_calls = 0
			MyGlobals.total_time_solver = 0
			MyGlobals.solver_configurations.clear()
			t1 = datetime.datetime.now()
			cnt +=1
			print('\nProcess %3d / %d pair ' % (cnt, len(function_pairs_list)))
			solution =  check_one_function_on_execute(contract_bytecode, contract_address, pair[0], pair[1], func_hash[pair[0]] if pair[0] in func_hash else pair[0], func_hash[pair[1]] if pair[1] in func_hash else pair[1], debug, read_from_blockchain)
			solution_dict[(pair[0], pair[1])] = solution
			t2 = datetime.datetime.now()
			sys.stdout.flush()
			if MyGlobals.ONE_CONTRACT_HB_TIMEOUT < int((t2 - MyGlobals.Time_checkpoint_HB).total_seconds()):
				print('\n', '\033[91m-------Finding the HB relations timed out\033[0m', '\n')
				break
	
	b = datetime.datetime.now()
	print('Time for HB pairs: ', b-a, '\n', '--'*50, '\n' )

	node_dict, temp_node_list, simplified_hb = find_nodes(function_pairs_list, impFunctionList, solution_dict ,contract_bytecode, contract_address, debug, read_from_blockchain)	

	return temp_node_list, simplified_hb	


def check_one_function_on_execute(contract_bytecode, contract_address, function1, function2, fn1, fn2, debug, read_from_blockchain):

	global fast_search, MAX_JUMP_DEPTH, MAX_CALL_DEPTH, symbolic_vars, good_jump_positions, solution_dict, max_solutions, solution_found	


	ops = parse_code( contract_bytecode, debug )
	if not code_has_instruction( ops, ['STOP', 'RETURN']) :
		#if debug: 
		print('\033[91m[-] The code does not have STOP or RETURN\033[0m')
		return False
	if debug: print_code( contract_bytecode, ops )

	print('\033[95m[ ] Finding HB for the pair  %s ,  %s :   %s , %s  \033[0m'%(fn1, fn2, function1, function2) )

	# Make the amount of sent Ether symbolic variable (can take any value)
	MyGlobals.symbolic_vars = ['CALLVALUE', 'NUMBER', 'GASLIMIT', 'TIMESTAMP', 'ADDRESS', 'ORIGIN', 'BLOCKHASH', 'BALANCE', 'CALLER']
	MyGlobals.solution_found = False
	MyGlobals.search_condition_found = False
	MyGlobals.stop_search = False

	if function2 == 'noHB':
		evmInstance = EVM(1, MyGlobals.max_jumpdepth_in_normal_search, False, contract_address, function1, function2, True, debug, read_from_blockchain)
		evmInstance.run_one_check(ops, 1)
		# run_one_check( 1, MyGlobals.max_jumpdepth_in_normal_search, False, ops, contract_address, function1, function2,  1, True,debug, read_from_blockchain )

	elif function1 == 'noHB':
		print('Function 2 should be noHB in any case \n')	
		return {}
	else:	
		evmInstance = EVM(1, MyGlobals.max_jumpdepth_in_normal_search, False, contract_address, function1, function2, False, debug, read_from_blockchain)
		evmInstance.run_one_check(ops, 1)
		# run_one_check( 1, MyGlobals.max_jumpdepth_in_normal_search, False, ops, contract_address, function1, function2,  1, False,debug, read_from_blockchain )
	
	soldict = {}

	if (function1, function2) in MyGlobals.solution_dict:
		print('\033[92m[+] Final Solution found \033[0m \n')
		i = 0

		for lists in MyGlobals.solution_dict[(function1, function2)]:
			i+=1
			mydict ={}

			for key, value in lists.iteritems():
				convert = True
				if 'input' in key:
					if 'inputlength' in key or not 'input-' in key:
						convert = False

				if convert:		
					if function1 in key:
						if not function1 in mydict:
							mydict[function1] = []
							key, value = changeContext(key, value, debug)
							mydict[function1].append((key, value))

						else:
							key, value = changeContext(key, value, debug)
							mydict[function1].append((key, value))

					if function2 in key and not function2=='noHB':
						if not function2 in mydict:
							mydict[function2] = []
							key, value = changeContext(key, value, debug)
							mydict[function2].append((key, value))

						else:
							key, value = changeContext(key, value, debug)
							mydict[function2].append((key, value))	


			soldict[i] = mydict	


		print_solution(function1, function2, fn1, fn2, soldict)
	else:
		print('\033[91m[-] No HB found for %s , %s  : %s , %s\033[0m ' % (fn1, fn2, function1, function2) )

	if MyGlobals.stop_search: 
		return soldict


	return {}

def find_nodes(function_pairs_list, funclist, solution_dict, contract_bytecode, contract_address, debug, read_from_blockchain):

	functionsHBList = []
	
	for pair in function_pairs_list:
		if (pair[0], pair[1]) in MyGlobals.solution_dict:
			
			if not pair[0] in functionsHBList:
				functionsHBList.append(pair[0])
			
			if not pair[1] in functionsHBList:
				functionsHBList.append(pair[1])

	funcitonsNoHBList = []
	funcitonsNoHBList = [x for x in funclist if not x in functionsHBList]

	for function in funcitonsNoHBList:
		MyGlobals.Time_checkpoint = datetime.datetime.now()
		solution_list =  check_one_function_on_execute(contract_bytecode, contract_address, function, 'noHB', function, 'noHB', debug, read_from_blockchain)
		solution_dict[(function, 'noHB')] = solution_list

	# Solution dict contains the entire HB relation details 

	# Construct a datastructure which stores all the nodes.
	temp_node_list = []
	node_dict = {}
	hb_list = []
	simplified_hb = []
	
	# print ('solution_dict', solution_dict, '\n', '--'*50, '\n')	
	for each_relation, solution_nodes in solution_dict.iteritems():

		for index, node in solution_nodes.iteritems():

			for fhash, fctx in node.iteritems():
				
				found = False
				for key, value in node_dict.iteritems():
					if value == {fhash:fctx}:
						found = True

				if not found:
					temp_dict = {}
					temp_dict['name'] = fhash

					for pair in fctx:
						temp_dict[pair[0]] = pair[1]

					temp_node_list.append(temp_dict)
					node_dict[len(temp_node_list)-1] = {fhash:fctx}

		if not each_relation[1] == 'noHB':
			
			for index, node in solution_nodes.iteritems():
				pair = ()
				reverse = False
				first = True
				for fhash, fctx in node.iteritems():
					if each_relation[1] == fhash and first:
						reverse = True	
					first = False	
					pair += (node_dict.keys()[node_dict.values().index({fhash:fctx})] ,)
	
				if reverse:
					hb_list.append((pair[1], pair[0]))

				else:
					hb_list.append(pair)	

				simplified_hb = optimize_hb(hb_list)	

	# Construct a hb list of pairs of nodes in HB
	
	print_nodes(node_dict)

	if debug: 
		print('List of nodes going to the fuzzer\n')
		for each in temp_node_list:
			print(each, '\n')

	if debug: print('Not simplified HB relations\n', hb_list, '\n')

	print('Simplified HB Relations -----\n', simplified_hb, '\n')

	return node_dict, temp_node_list, simplified_hb
