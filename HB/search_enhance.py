from __future__ import print_function
from execute_block import run_one_check
from values import get_params, set_params, initialize_params, print_params, MyGlobals, clear_globals
from parse_code import *
import datetime
import sys

def cartesian(lists):
	if lists == []: return [()]
	return [x + (y,) for x in cartesian(lists[:-1]) for y in lists[-1]]

def stateChangingFunctions(fullfunclist, contract_bytecode, contract_address, read_from_blockchain, debug):
	global symbolic_vars, solution_found, stop_search, max_jumpdepth_in_normal_search


	funclist = [temp[1] for temp in fullfunclist]
	func_hash = {}
	for f in fullfunclist:
		if isinstance(f[0],str):
			func_hash[f[1]]= f[0]


	ops = parse_code( contract_bytecode, debug )
	if not code_has_instruction( ops, ['STOP', 'RETURN']) :
		#if debug: 
		print('\033[91m[-] The code does not have STOP or RETURN\033[0m')
		return False
	if debug: print_code( contract_bytecode, ops )

	impFunctionList = []
	cnt = 0
	for function_hash in funclist:
		cnt +=1
		MyGlobals.symbolic_vars = ['CALLVALUE', 'NUMBER', 'GASLIMIT', 'TIMESTAMP', 'ADDRESS', 'ORIGIN', 'BLOCKHASH', 'CALLER']
		MyGlobals.solution_found = False
		MyGlobals.search_condition_found = False
		MyGlobals.stop_search = False
		function1 = function_hash	
		function2 = function_hash
		importantFunc1 = False
		importantFunc2 = False
		print('\033[94m[ ] Check %3d / %3d :  whether %s {%s} can change the state \033[0m'%(cnt, len(funclist), func_hash[function1] if function1 in func_hash else function1, function1) )
		sys.stdout.flush()

		MyGlobals.MAX_JUMP_DEPTH = 50
		MyGlobals.MAX_VISITED_NODES = 2000
		MyGlobals.solver_configurations.clear()
		MyGlobals.Time_checkpoint = datetime.datetime.now()
		MyGlobals.ONE_HB_TIMEOUT = 1*60
		importantFunc1 = run_one_check( 1, MyGlobals.max_jumpdepth_in_normal_search, True, ops, contract_address, function1, function2,  1, False, debug, read_from_blockchain )
		t2 = datetime.datetime.now()
		if MyGlobals.ONE_CONTRACT_HB_TIMEOUT < int((t2 - MyGlobals.Time_checkpoint_HB).total_seconds()):
			return [], []	
		MyGlobals.MAX_JUMP_DEPTH = 50
		MyGlobals.MAX_VISITED_NODES = 20000
		MyGlobals.jumpi_switch = False	
		MyGlobals.solution_found = False
		MyGlobals.last_eq_func = -1
		sys.stdout.flush()

		# if importantFunc:

		# 	print('\033[92m [+] %s can change the state \n \033[0m'%(function1) )
		# 	impFunctionList.append(function_hash)
	

		# else:
			# MyGlobals.set_storage_symbolic = True
		# if not function_hash == 'fallback':	
		MyGlobals.MAX_JUMP_DEPTH = 50
		MyGlobals.MAX_VISITED_NODES = 2000
		MyGlobals.set_storage_symbolic = True			
		MyGlobals.solver_configurations.clear()
		MyGlobals.Time_checkpoint = datetime.datetime.now()
		MyGlobals.ONE_HB_TIMEOUT = 1*60
		importantFunc2 = run_one_check( 1, MyGlobals.max_jumpdepth_in_normal_search, True, ops, contract_address, function1, function2,  1, False, debug, read_from_blockchain )
		t2 = datetime.datetime.now()
		if MyGlobals.ONE_CONTRACT_HB_TIMEOUT < int((t2 - MyGlobals.Time_checkpoint_HB).total_seconds()):
			return [], []
		MyGlobals.MAX_JUMP_DEPTH = 10000
		MyGlobals.MAX_VISITED_NODES = 50000
		MyGlobals.jumpi_switch = False
		MyGlobals.set_storage_symbolic = False
		MyGlobals.solution_found = False	

		if importantFunc1 or importantFunc2:
			print('\033[92m[+] %s can change the state \n \033[0m'%(func_hash[function1] if function1 in func_hash else function1) )
			impFunctionList.append(function_hash)

		else:
			print('\033[91m[-] %s cannot change the state \n \033[0m'%(func_hash[function1] if function1 in func_hash else function1) )	
			
	return stateChangingFunctionPairs(impFunctionList)


def stateChangingFunctionPairs(impFunctionList):

	function_pairs_list = cartesian([impFunctionList, impFunctionList])
	new_list = []
	newfunclist = []

	for each_pair in function_pairs_list:
		if not each_pair[0]==each_pair[1]:
			if each_pair[0] in MyGlobals.funcvardata and each_pair[1] in MyGlobals.funcvardata:

				print(each_pair[0], each_pair[1], MyGlobals.funcvardata[each_pair[0]])	
				for key, value in MyGlobals.funcvardata[each_pair[0]].iteritems():

					if key in MyGlobals.funcvardata[each_pair[1]]:
						if 'W' in MyGlobals.funcvardata[each_pair[1]][key] or 'W' in MyGlobals.funcvardata[each_pair[0]][key]:
							if not (each_pair[0], each_pair[1]) in new_list:
								new_list.append((each_pair[0], each_pair[1]))
								if not each_pair[0] in newfunclist:
									newfunclist.append(each_pair[0])
								if not each_pair[1] in newfunclist:
									newfunclist.append(each_pair[1])	

								
	return newfunclist, new_list	


