from __future__ import print_function
import os
import sys
import re
from execute_instruction import *
from values import get_params, initialize_params, print_params
from values import MyGlobals, clear_globals, update_global_datastructures
from misc import *
import random
from random import shuffle
import datetime
random.seed(datetime.datetime.now())
import z3
from z3 import *

class EVM(EVMCore):
	
	def __init__(self, max_call_depth, max_jump_depth, search_enhance, contract_address, function1, function2, noHB, debug, read_from_blockchain):
		self.max_call_depth = max_call_depth
		self.max_jump_depth = max_jump_depth
		self.search_enhance = search_enhance
		self.contract_address = contract_address
		self.function1 = function1
		self.function2 = function2
		self.noHB = noHB
		self.debug = debug
		self.read_from_blockchain = read_from_blockchain

	def function_accept(self, op, stack, trace, debug):
		op_name = op['o']
		op_val = op['input']

		return True, False

	def function_throw(self, op, stack, trace, debug ):


		op_name = op['o']
		op_val = op['input']

		if 'JUMP' in op_name:

			if is_fixed(stack[-1]):

				if get_value(stack[-1]) == 0:
					return True, False	
							
				else:
					return False, False

			else:
				return False, False				

		return True, False	

	def function_sstore(self, op, stack, trace, debug):
		
		op_name = op['o']
		op_val = op['input']	
		return True, True

	def add_additional_conditions(self, solver, sha3_values):
		for sym_var, concrete_val in sha3_values.iteritems():

			if len(concrete_val) == 1:
				temp_conc =BitVecVal(int(concrete_val[0]), 256)
				temp_sym = BitVec(sym_var, 256)
				solver.add(If(temp_sym == temp_conc,  BitVecVal(1, 256),  BitVecVal(0, 256)) == BitVecVal(1,256) )

			elif len(concrete_val) >1:
				p = BitVec('p', 256)
				formula = BitVecVal(0, 256)
				temp_sym = BitVec(sym_var, 256)

				for each_value in concrete_val:
					each_value = BitVecVal(int(each_value), 256)
					formula = (simplify(formula) | simplify(If(temp_sym == each_value, BitVecVal(1, 256), BitVecVal(0, 256))))

				print(formula, 'in formula\n')
				solver.add( formula == BitVecVal(1, 256) )
			
			else:
				print('Not able to add conditions\n')

		return		


	def new_state(self, stack, storage, sha3_dict, sha3_values, mmemory, trace, data):
		datastructures = {}
		datastructures['stack'] = copy.deepcopy(stack)
		datastructures['storage'] = copy.deepcopy(storage)
		datastructures['sha3_dict'] = copy.deepcopy(sha3_dict)
		datastructures['data'] = copy.deepcopy(data)
		datastructures['sha3_values'] = copy.deepcopy(sha3_values)

		return datastructures

	def  run_one_check(self, ops, key, datastructures = {}):


		global MAX_JUMP_DEPTH, MAX_CALL_DEPTH, fast_search, search_condition_found, solution_found

		# Stop the search once it exceeds timeout
		time_now = datetime.datetime.now()

		if MyGlobals.ONE_HB_TIMEOUT < int((time_now - MyGlobals.Time_checkpoint).total_seconds()):
			MyGlobals.stop_search = True
			return

		MyGlobals.MAX_JUMP_DEPTH 	= max_jump_depth
		MyGlobals.MAX_CALL_DEPTH 	= max_call_depth
		configurations = {}

		if 1 == key:
			print('[ ] Started executing 1st tree... ')
			clear_globals()

			storage = {}    
			stack   = []
			mmemory = {}
			data = {}
			trace   = []
			sha3_dict = {}
			sha3_values = {}
			function_hash = function1

			if search_enhance:
				MyGlobals.s.push()
				self.execute_one_block(ops,stack,0, trace, storage, mmemory, data, configurations, sha3_dict, sha3_values, ['SSTORE', 'CALL', 'DELEGATECALL', 'CALLCODE', 'SUICIDE'], function_sstore, 0, 0, function_hash, False, key )
				MyGlobals.s.pop()
				
				return MyGlobals.solution_found
			
			if noHB:
				MyGlobals.s.push()
				self.execute_one_block(ops,stack,0, trace, storage, mmemory, data, configurations, sha3_dict, sha3_values, ['STOP', 'RETURN', 'SUICIDE'], function_accept, 0, 0, function_hash, True, key )
				MyGlobals.s.pop()	
				return		
		
			MyGlobals.s = MyGlobals.s1	
			MyGlobals.s.push()
			self.execute_one_block(ops,stack,0, trace, storage, mmemory, data, configurations, sha3_dict, sha3_values, ['STOP', 'RETURN'], function_accept, 0, 0, function_hash, False, key )
			MyGlobals.s.pop()
			print('\033[94m[+] Finished executing 1st tree... \033[0m')
			print('\033[92m    Visited %d nodes\033[0m'%(MyGlobals.visited_nodes))
			return
			function_hash = function2
		
		if 2 == key:
			print('\033[92m    Visited %d nodes\033[0m'%(MyGlobals.visited_nodes))
			print('[ ] Started executing 2nd tree... ')
			function_hash = function2	
			stack = []
			storage2 = copy.deepcopy(datastructures['storage'])
			sha3_dict2 = copy.deepcopy(datastructures['sha3_dict'])
			sha3_values2 = copy.deepcopy(datastructures['sha3_values'])
			data2 = copy.deepcopy(datastructures['data'])
			mmemory = {}
			trace   = []
			MyGlobals.search_condition_found = False
			MyGlobals.stop_search = False

			# Setting up the solvers
			
			MyGlobals.s2.reset()
			MyGlobals.s = MyGlobals.s2
			MyGlobals.s.push()
			MyGlobals.s.add(If(UGT(BitVec(('TIMESTAMP'+'-'+str(1)+'-'+function2),256), BitVec(('TIMESTAMP'+'-'+str(1)+'-'+function1), 256)), BitVecVal(1, 256),  BitVecVal(0, 256)) == BitVecVal(1,256))
			MyGlobals.s.add(If(UGT(BitVec(('NUMBER'+'-'+str(1)+'-'+function2),256), BitVec(('NUMBER'+'-'+str(1)+'-'+function1), 256)), BitVecVal(1, 256),  BitVecVal(0, 256)) == BitVecVal(1,256))
			MyGlobals.s.add(If(BitVec(('TIMESTAMP'+'-'+str(1)+'-'+function2),256) == BitVecVal(315, 256) * BitVec(('NUMBER'+'-'+str(1)+'-'+function2),256), BitVecVal(1, 256),  BitVecVal(0, 256)) == BitVecVal(1,256) )
			MyGlobals.s.add(If(BitVec(('TIMESTAMP'+'-'+str(1)+'-'+function1),256) == BitVecVal(315, 256) * BitVec(('NUMBER'+'-'+str(1)+'-'+function1),256), BitVecVal(1, 256),  BitVecVal(0, 256)) == BitVecVal(1,256) )

			self.execute_one_block(ops,stack,0, trace, storage2, mmemory, data2, configurations, sha3_dict2, sha3_values2,  ['STOP', 'RETURN'], function_accept, 0, 0, function_hash, True, key )
			MyGlobals.s.pop()

			MyGlobals.s = MyGlobals.s1
			print('\033[94m[+] Finished executing 2nd tree... \033[0m')

			return

		if 3 == key:
			print('\033[92m    Visited %d nodes\033[0m'%(MyGlobals.visited_nodes))	
			print('[ ] Started executing 3rd tree... ')
			function_hash = function2
			stack = []
			storage3 = {}
			sha3_dict3 = copy.deepcopy(datastructures['sha3_dict'])
			sha3_values3 = copy.deepcopy(datastructures['sha3_values'])
			data3 = copy.deepcopy(datastructures['data'])
			mmemory   = {}
			trace = []
			MyGlobals.search_condition_found = False
			MyGlobals.stop_search = False

			MyGlobals.s.push()
			self.execute_one_block(ops,stack,0, trace, storage3, mmemory, data3, configurations, sha3_dict3, sha3_values3,  ['JUMP', 'JUMPI', 'REVERT'], function_throw, 0, 0, function_hash, True, key )
			MyGlobals.s.pop()

			print('\033[94m[+] Finished executing 3rd tree... \033[0m')
			
			if not MyGlobals.solution_found:
				print('\033[92m    Visited %d nodes\033[0m'%(MyGlobals.visited_nodes))
				print('[ ] Started executing 3rd tree... ')
				function_hash = function2
				stack[:] = []
				storage3.clear()
				sha3_dict3 = copy.deepcopy(datastructures['sha3_dict'])
				sha3_values3 = copy.deepcopy(datastructures['sha3_values'])
				data3 = copy.deepcopy(datastructures['data'])
				mmemory.clear()
				trace[:] = []
				MyGlobals.search_condition_found = False
				MyGlobals.stop_search = False

				MyGlobals.s.push()
				self.execute_one_block(ops,stack,0, trace, storage3, mmemory, data3, configurations, sha3_dict3, sha3_values3,  ['STOP', 'RETURN'], function_accept, 0, 0, function_hash, False,  key )
				MyGlobals.s.pop()
			
			if MyGlobals.in_sha3>0 and MyGlobals.solution_found:
				return

			MyGlobals.solution_found = False

			return

		if 4 == key:
			print('\033[92m    Visited %d nodes\033[0m'%(MyGlobals.visited_nodes))
			print('[ ] Started executing 4th tree... ')
			function_hash = function1
			stack = []
			storage4 = copy.deepcopy(datastructures['storage'])
			sha3_dict4 = copy.deepcopy(datastructures['sha3_dict'])
			sha3_values4 = copy.deepcopy(datastructures['sha3_values'])
			data4 = copy.deepcopy(datastructures['data'])
			mmemory = {}
			trace   = []
			MyGlobals.search_condition_found = False
			MyGlobals.stop_search = False
			
			# Setting up the solvers
			MyGlobals.s = Solver()
			MyGlobals.s = MyGlobals.s1
			MyGlobals.s.push()
			MyGlobals.s.push()
			self.execute_one_block(ops,stack,0, trace, storage4, mmemory, data4, configurations, sha3_dict4, sha3_values4,  ['JUMP', 'JUMPI', 'REVERT'], function_throw, 0, 0, function_hash, True, key )
			MyGlobals.s.pop()
			print('\033[94m[+] Finished executing 4th tree... \033[0m')

			MyGlobals.s = MyGlobals.s2

			if MyGlobals.in_sha3>0  and MyGlobals.solution_found:
				return
			MyGlobals.solution_found = False
			return

		return		
		
	def self.execute_one_block(self, ops , stack , pos , trace, storage, mmemory, data, configurations,  sha3_dict,  sha3_values, search_op, search_function, jumpdepth, calldepth, function_hash, find_solution,  key):

		sys.stdout.flush()

		global s, d, stop_search, search_condition_found, visited_nodes, st,  MAX_JUMP_DEPTH, MAX_CALL_DEPTH, fast_search, solution_found, max_solutions, solution_dict

		actual_key = 0
		if key in [1, 4]: actual_key = 1
		if key in [2, 3]: actual_key = 2
		jump_condition = False

		if MyGlobals.stop_search : return 

		MyGlobals.visited_nodes += 1
		if MyGlobals.visited_nodes > MyGlobals.MAX_VISITED_NODES: return
		
		# Stop the search once it exceeds timeout
		time_now = datetime.datetime.now()
		if MyGlobals.ONE_HB_TIMEOUT < int((time_now - MyGlobals.Time_checkpoint).total_seconds()):
			MyGlobals.stop_search = True
			return
		if MyGlobals.ONE_CONTRACT_HB_TIMEOUT < int((time_now - MyGlobals.Time_checkpoint_HB).total_seconds()):
			MyGlobals.stop_search = True
			return	
			
		# Execute the next block of operations
		first = True
		newpos = pos
		while (first or newpos != pos) and not MyGlobals.stop_search:


			first = False
			pos = newpos	
				
			# If no more code, then stop
			if pos >= len(ops) or pos < 0:
				if debug: print('\033[94m[+] Reached bad/end of execution\033[0m')
				return False

			# Debug info
			if debug: print('[ %3d %3d %5d] : %4x : %12s : %s  ' % (calldepth, jumpdepth, MyGlobals.visited_nodes, ops[pos]['id'], ops[pos]['o'], ops[pos]['input']), search_op )


			# Check if calldepth or jumpdepth should be changed 
			# and stop the search if certain conditions are met
			if pos == 0: 
				calldepth += 1
				jumpdepth = 0
			if ops[pos]['o'] == 'JUMPDEST': jumpdepth += 1
			if( jumpdepth > MyGlobals.MAX_JUMP_DEPTH): 
				if debug:print ('\033[95m[-] Reach MAX_JUMP_DEPTH\033[0m' , jumpdepth,  MyGlobals.MAX_JUMP_DEPTH)
				return
			if( calldepth > MyGlobals.MAX_CALL_DEPTH): 
				if debug:print ('\033[95m[-] Reach MAX_CALL_DEPTH\033[0m' )
				return




			# Check if configuration exist if 
			# - it is the first instruction in the code (the code restarted)
			# - it is jumpdest
			# - it is the first instruction after JUMPI 
			# if pos == 0 or ops[pos]['o'] == 'JUMPDEST' or (pos > 0 and ops[pos-1]['o'] == 'JUMPI'):
			# 	if seen_configuration( configurations, ops, pos, stack, mmemory, storage): 
			# 		if debug:print ('\033[95m[-] Seen configuration\033[0m' )
			# 		return
			
		

			# Check if the current op is one of the search ops
			if ops[pos]['o'] in search_op:

				if debug:
					print('\033[96m[+] Reached %s at %x \033[0m'  % (ops[pos]['o'], ops[pos]['id'] ) )

				# If JUMPI is the search op and a push2 0000 before it, ensure that we add the additional condition on the stack to check for satisfiability.
				if 'JUMPI' == ops[pos]['o'] and 'JUMPI' in search_op:
					if is_fixed(stack[-1]):
						if get_value(stack[-1]) == 0:
							jump_condition = True

				new_search_condition_found, stop_expanding_the_search_tree = False, False

				if search_enhance:
					new_search_condition_found, stop_expanding_the_search_tree =  search_function( ops[pos] , stack , trace, debug )

				else:	
					new_search_condition_found, stop_expanding_the_search_tree =  search_function( ops[pos] , stack , trace, debug )
					
				MyGlobals.search_condition_found = MyGlobals.search_condition_found or new_search_condition_found

				if MyGlobals.search_condition_found and search_enhance:
					MyGlobals.solution_found = True
				
				# In case there is a probability of finding a solution we need to add the additional constraints to the solver before finding the solutions. 
				if MyGlobals.search_condition_found and not search_enhance:
					self.add_additional_conditions(MyGlobals.s, sha3_values)
					# If jump_condition is True then add the addtional condition of JUMPI to the global solver to retrieve solutions.
					if jump_condition:
						temp = copy.deepcopy(stack[-2])
						MyGlobals.s.push()
						MyGlobals.s.add(temp['z3']!=0)


				if MyGlobals.search_condition_found and (not search_enhance) and (not noHB) and ((key ==1 or key ==2) or (key ==3 and not find_solution)) and (not jump_condition):

					# Save the state of execution before calling next tree
					datastructures = self.new_state(stack, storage, sha3_dict, sha3_values, mmemory, trace, data)
					MyGlobals.s.push()
					self.run_one_check(ops, key+1, datastructures)
	 				MyGlobals.s.pop()
					return




				if MyGlobals.search_condition_found and (noHB or (key == 3 and find_solution) or key == 4) and find_solution:
					solution = get_function_calls( calldepth, key, function_hash, function1, function2 ,debug )
					
					if not solution:
						# In case of jump condition, the control should not be returned to the caller of execute_block. Instead, callee function continues to execute.
						if not jump_condition:
							return 

						else:
							MyGlobals.s.pop()
							jump_condition = False
							MyGlobals.search_condition_found = False

					else:

						MyGlobals.solution_found = True

						if noHB:
							if not (function1, 'noHB') in MyGlobals.solution_dict:
								MyGlobals.solution_dict[(function1, function2)] = []
							
							if not solution in MyGlobals.solution_dict[(function1, 'noHB')] and len(MyGlobals.solution_dict[(function1, 'noHB')]) <  1:
								MyGlobals.solution_dict[(function1, function2)].append(solution)	

							if len(MyGlobals.solution_dict[(function1, function2)]) == 1:
								MyGlobals.stop_search = True
							
							return	
							
						if not (function1, function2) in MyGlobals.solution_dict:
							MyGlobals.solution_dict[(function1, function2)] = []

						# if not solution in MyGlobals.solution_dict[(function1, function2)] and len(MyGlobals.solution_dict[(function1, function2)]) < MyGlobals.max_solutions:
						if solution_filter(solution, function1, function2):	
							MyGlobals.ONE_HB_TIMEOUT = 2*60
							MyGlobals.solution_dict[(function1, function2)].append(solution)
		
							
						if len(MyGlobals.solution_dict[(function1, function2)]) == MyGlobals.max_solutions:
							MyGlobals.stop_search = True

						# In case of jump condition, the stack has to be cleared with the extra jump condition before handling JUMPI operation in its usual way.	
						if jump_condition and not len(MyGlobals.solution_dict[(function1, function2)]) == MyGlobals.max_solutions:
							MyGlobals.s.pop()
							jump_condition = False
							MyGlobals.search_condition_found = False
						

						else:	
							return

				if jump_condition:		
					jump_condition = False		

			# Execute the next operation
			newpos, halt = execute( ops, stack, pos, storage, mmemory, data, trace, calldepth, function_hash, key, search_enhance,debug, read_from_blockchain  )


			# If halt is True, then the execution should stop 
			if halt:
			
				if debug: print('\033[94m[+] Halted on %s on line %x \033[0m' % (ops[pos]['o'],ops[pos]['id']))
				
				# if MyGlobals.stop_search: print('Search condition found \n')
				# if not MyGlobals.stop_search: print('Search condition not found \n')									
				# If normal stop 
				if ops[pos]['o'] in ['STOP','RETURN','SUICIDE']:

					# If search condition still not found then call again the contract
					# (infinite loop is prevented by calldepth )
					if not MyGlobals.search_condition_found:
						return

					# Else stop the search
					else:
						if search_enhance:
							MyGlobals.solution_found = True
							return

						self.add_additional_conditions(MyGlobals.s, sha3_values)

						if (not search_enhance) and (not noHB) and ((key ==1 or key ==2) or (key ==3 and 'STOP' in search_op)):
							# Save the state of execution before calling next tree
							datastructures = self.new_state(stack, storage, sha3_dict, sha3_values, mmemory, trace, data)
							MyGlobals.s.push()
							self.run_one_check( ops, key+1, datastructures )	
							MyGlobals.s.pop()

						if find_solution and (noHB or (key == 3 and find_solution)) or key == 4:
							solution = get_function_calls( calldepth, key, function_hash, function1, function2, debug )
							if not solution:
								return
							MyGlobals.solution_found = True
							print(solution)
							if noHB:
								if not (function1, 'noHB') in MyGlobals.solution_dict:
									MyGlobals.solution_dict[(function1, function2)] = []
								
								if not solution in MyGlobals.solution_dict[(function1, 'noHB')] and len(MyGlobals.solution_dict[(function1, 'noHB')]) <  2:
									MyGlobals.solution_dict[(function1, function2)].append(solution)	

								if len(MyGlobals.solution_dict[(function1, function2)]) == 2:
									MyGlobals.stop_search = True

								return	

							if not (function1, function2) in MyGlobals.solution_dict:
								MyGlobals.solution_dict[(function1, function2)] = []

							# if not solution in MyGlobals.solution_dict[(function1, function2)] and len(MyGlobals.solution_dict[(function1, function2)]) < MyGlobals.max_solutions:
							if solution_filter(solution, function1, function2):	
								MyGlobals.ONE_HB_TIMEOUT = 2*60
								MyGlobals.solution_dict[(function1, function2)].append(solution)

							if len(MyGlobals.solution_dict[(function1, function2)]) == MyGlobals.max_solutions:
								MyGlobals.stop_search = True


						return


				# In all other cases stop further search in this branch of the tree
				else:
					return 
		
			# If program counter did not move 
			# It means either:
			# 1) we need to branch
			# 2) unknown instruction
			if pos == newpos:
			
				si = ops[pos]

				# It can be JUMPI
				if si['o'] == 'JUMPI':
					if len(stack) < 2:
						if debug: print('\033[95m[-] In JUMPI (line %x) the stack is too small to execute JUMPI\033[0m' % pos )
						return False
			
					addr = stack.pop()
					des = stack.pop()

					if is_undefined(des):
						if debug: print('\033[95m[-] In JUMPI the expression cannot be evaluated (is undefined)\033[0m'   )
						return False

					sole = '  * sole * '

					fallback_frame = False

					#
					# Branch when decision is incorrect (no need to compute the addresses)		
					#

					# In the fast search mode, the jumpi pos + 1 must be in the list of good jump positions
					# if is_good_jump( ops, pos+1, debug ): 

					MyGlobals.s.push()
					MyGlobals.s.add( des['z3'] == 0)
					try:
						
						# We want to switch off the check for jumpi while we are searching for functions which can change the global state.
						# But, we will switch off the jumpi check only when the execution of the desired function starts.

						if (MyGlobals.jumpi_switch and search_enhance):

							if debug: print ('Now searching without jumpi check : Branch 1\n')
							storage2 = copy.deepcopy(storage)
							stack2 = copy.deepcopy(stack)
							trace2 = copy.deepcopy(trace)
							mmemory2 = copy.deepcopy(mmemory)
							data2 = copy.deepcopy(data)
							sha3_values2 = copy.deepcopy(sha3_values)
							sha3_dict2 = copy.deepcopy(sha3_dict)

							if debug: print('\t'*8+'-'*20+'JUMPI branch 1 (go through)')
							sole = ''

							self.execute_one_block(ops,stack2,	pos + 1, 	trace2, storage2, 	mmemory2, data2, configurations,  sha3_dict2, sha3_values2, search_op, search_function, jumpdepth+1, calldepth,  function_hash, find_solution,  key )
							MyGlobals.search_condition_found = False

						else:	
							MyGlobals.num_solver_calls+=1
							time1 = datetime.datetime.now()

							satisfied = False
							temps = Solver()
							temps.add(MyGlobals.s.assertions())
							if temps in MyGlobals.solver_configurations:
								satisfied = MyGlobals.solver_configurations[temps]
								print('found solver')

							else:
								if MyGlobals.s.check() == sat:
									satisfied = True
									MyGlobals.solver_configurations[temps] = satisfied

								else:
									satisfied = False
									MyGlobals.solver_configurations[temps] = satisfied

							if satisfied:
								if (MyGlobals.last_eq_func) == long(int(MyGlobals.functions[len(MyGlobals.functions)-1][1], 16)) and (MyGlobals.set_storage_symbolic) and function_hash in ['11111111', '22222222']:
									MyGlobals.jumpi_switch = True
									MyGlobals.last_eq_func = -1
									fallback_frame = True

								time2 = datetime.datetime.now()
								MyGlobals.total_time_solver+=(time2-time1).total_seconds()

								if debug: print ('Now searching with jumpi check : Branch 1\n')

								storage2 = copy.deepcopy(storage)
								stack2 = copy.deepcopy(stack)
								trace2 = copy.deepcopy(trace)
								mmemory2 = copy.deepcopy(mmemory)
								data2 = copy.deepcopy(data)
								sha3_values2 = copy.deepcopy(sha3_values)
								sha3_dict2 = copy.deepcopy(sha3_dict)

								if debug: print('\t'*8+'-'*20+'JUMPI branch 1 (go through)')

								sole = ''
								self.execute_one_block(ops,stack2,	pos + 1, 	trace2, storage2, 	mmemory2, data2, configurations,  sha3_dict2, sha3_values2, search_op, search_function, jumpdepth+1, calldepth,  function_hash, find_solution,  key )
								MyGlobals.search_condition_found = False

								if MyGlobals.jumpi_switch : MyGlobals.jumpi_switch = False

							else:
								time2 = datetime.datetime.now()
								MyGlobals.total_time_solver+=(time2-time1).total_seconds()

					except Exception as e:
						print ("Exception: "+str(e))

					MyGlobals.s.pop()


					if MyGlobals.stop_search: return

					#
					# Branch when the decision is possibly correct
					#
					if not is_fixed(addr):
						# for statistics
						if not search_enhance:
							if 'jumpi_addr' in MyGlobals.notimplemented_ins:
								MyGlobals.notimplemented_ins['jumpi_addr']+=1
							else:
								MyGlobals.notimplemented_ins['jumpi_addr']=1

						if debug: print('\033[95m[-] In JUMPI the jump address cannot be determined \033[0m'  % jump_dest )
						return False
		
					jump_dest = get_value( addr )
					if( jump_dest <= 0):
						if debug: print('\033[95m[-] The jump destination is not a valid address : %x\033[0m'  % jump_dest )
						return False

					new_position= find_pos(ops, jump_dest )
					if( new_position < 0):
						if debug: print('\033[95m[-] The code has no such jump destination: %s at line %x\033[0m' % (hex(jump_dest), si['id']) )
						return False


					# In the fast search mode, the jumpi new_position must be in the list of good jump positions
					# if is_good_jump( ops, new_position, debug ): 

					MyGlobals.s.push()
					MyGlobals.s.add( des['z3'] != 0)
					
					try:
						if fallback_frame: return

						# If already in sha3 and solution found do not branch
						if MyGlobals.solution_found and MyGlobals.in_sha3>0 :
							MyGlobals.s.pop()
							return

						if (MyGlobals.jumpi_switch and search_enhance ):
							if debug: print ('Now searching without jumpi check : Branch 2\n')

							if debug:
								if ops[pos]['id'] -  MyGlobals.last_eq_step < 5:
									print('\t'*8+'-'*18+'\033[96m %2d Executing function %x \033[0m' % (calldepth, MyGlobals.last_eq_func) )


							storage2 = copy.deepcopy(storage)
							stack2 = copy.deepcopy(stack)
							trace2 = copy.deepcopy(trace)
							mmemory2 = copy.deepcopy(mmemory)
							data2 = copy.deepcopy(data)
							sha3_values2 = copy.deepcopy(sha3_values)
							sha3_dict2 = copy.deepcopy(sha3_dict)

							if debug: print( ('\t'*8+'-'*20+'JUMPI branch 2 (jump) on step %x' + sole ) % ops[pos]['id'] )


							self.execute_one_block(ops,stack2,	new_position, 	trace2, storage2, 	mmemory2, data2, configurations,  sha3_dict2, sha3_values2, search_op, search_function,  jumpdepth, calldepth, function_hash, find_solution, key )
							MyGlobals.search_condition_found = False


						else:	
							MyGlobals.num_solver_calls+=1
							time1 = datetime.datetime.now()

							satisfied = False
							temps = Solver()
							temps.add(MyGlobals.s.assertions())
							if temps in MyGlobals.solver_configurations:
								satisfied = MyGlobals.solver_configurations[temps]
								print('found solver')

							else:
								
								if MyGlobals.s.check() == sat:
									satisfied = True
									MyGlobals.solver_configurations[temps] = satisfied

								else:
									satisfied = False
									MyGlobals.solver_configurations[temps] = satisfied

							if satisfied:
								time2 = datetime.datetime.now()
								MyGlobals.total_time_solver+=(time2-time1).total_seconds()

								if debug: print ('Now searching with jumpi check : Branch 2\n')

								if (not function_hash == '11111111') and (not function_hash == '22222222'):
									if (MyGlobals.last_eq_func) == long(int(function_hash, 16)) and (MyGlobals.set_storage_symbolic):
										MyGlobals.jumpi_switch = True

								if debug:
									if ops[pos]['id'] -  MyGlobals.last_eq_step < 5:
										print('\t'*8+'-'*18+'\033[96m %2d Executing function %x \033[0m' % (calldepth, MyGlobals.last_eq_func) )


								storage2 = copy.deepcopy(storage)
								stack2 = copy.deepcopy(stack)
								trace2 = copy.deepcopy(trace)
								mmemory2 = copy.deepcopy(mmemory)
								data2 = copy.deepcopy(data)
								sha3_values2 = copy.deepcopy(sha3_values)
								sha3_dict2 = copy.deepcopy(sha3_dict)

								if debug: print( ('\t'*8+'-'*20+'JUMPI branch 2 (jump) on step %x' + sole ) % ops[pos]['id'] )


								self.execute_one_block(ops,stack2,	new_position, 	trace2, storage2, 	mmemory2, data2, configurations,  sha3_dict2, sha3_values2, search_op, search_function,  jumpdepth, calldepth, function_hash, find_solution, key )
								MyGlobals.search_condition_found = False

								if MyGlobals.jumpi_switch : MyGlobals.jumpi_switch = False

							else:
								time2 = datetime.datetime.now()
								MyGlobals.total_time_solver+=(time2-time1).total_seconds()	


					except Exception as e:
						print ("Exception: "+str(e))

					MyGlobals.s.pop()
					
					return 

				# It can be CALLDATALOAD
				elif si['o'] == 'CALLDATALOAD':

					addr = stack.pop()

					# First find the symbolic variable name
					text = str(addr['z3'])
					regex = re.compile('input[0-9]*\[[0-9 ]*\]-[1-2]-[0-9a-f]{8}')
					match = re.search( regex, text)
					if match:
						sm = text[match.start():match.end()]

						# assign random (offset) address as value for the variable
						random_address = get_hash(sm) >> 64
						
						r2 = re.compile('\[[0-9 ]*\]')
						indmat = re.search( r2, sm )
						index = -2
						if indmat:
							index = int( sm[indmat.start()+1:indmat.end()-1] )



						total_added_to_solver = 0

						# add 'd' at the end of the name of the symbolic variable (used later to distinguish them)
						if index>= 0 and ('data-'+str(calldepth)+'-'+str(index)+'-'+str(actual_key)+'-'+function_hash) in data:
							data[('data-'+str(calldepth)+'-'+str(index)+'-'+str(actual_key)+'-'+function_hash)] = BitVec(sm+'d',256)
							MyGlobals.s.push()
							MyGlobals.s.add( data[('data-'+str(calldepth)+'-'+str(index)+'-'+str(actual_key)+'-'+function_hash)] == random_address  )
							total_added_to_solver = 1


						# replace the variable with concrete value in stack and memory
						for st in stack:
							if 'z3' in st:
								st['z3'] = simplify(substitute( st['z3'], (BitVec(sm,256),BitVecVal(random_address, 256))))
						for st in mmemory:
							if 'z3' in mmemory[st]:
								mmemory[st]['z3'] = simplify(substitute( mmemory[st]['z3'], (BitVec(sm,256),BitVecVal(random_address, 256))))

						# replace in the address as well
						addr = simplify(substitute(addr['z3'], (BitVec(sm,256),BitVecVal(random_address, 256)) ) )

						# Branch
						branch_array_size = [0,1,2]
						for one_branch_size in branch_array_size:
							# do not branch if solution found and in sha3
							if MyGlobals.solution_found and MyGlobals.in_sha3>0 :
								for tempp in range(total_added_to_solver):
									MyGlobals.s.pop()
								return

							storage2 = copy.deepcopy(storage)
							stack2 = copy.deepcopy(stack)
							trace2 = copy.deepcopy(trace)
							mmemory2 = copy.deepcopy(mmemory)
							data2 = copy.deepcopy(data)
							sha3_values2 = copy.deepcopy(sha3_values)
							sha3_dict2 = copy.deepcopy(sha3_dict)

							data2['data-' + str(actual_key) + '-' + str(addr) + '-' + function_hash] = BitVecVal(one_branch_size,256)
							for i in range(one_branch_size):
								data2['data-'+str(actual_key)+'-'+ str(addr.as_long()+32+32*i)  + '-'+function_hash] = BitVec('input'+str(actual_key)+'['+('%s'%(addr.as_long()+32+32*i))+']' +'-'+function_hash,256)

							stack2.append( {'type':'constant','step':ops[pos]['id'], 'z3':BitVecVal( one_branch_size, 256)})

							MyGlobals.s.push()
							MyGlobals.s.add( BitVec('input'+str(actual_key)+('[%x'%addr.as_long())+']' +'-'+function_hash,256) == one_branch_size)

							self.execute_one_block(ops,stack2,	pos+1, 	trace2, storage2, 	mmemory2, data2, configurations, sha3_dict2, sha3_values2,	search_op, search_function,  jumpdepth, calldepth, function_hash, find_solution, key )
							MyGlobals.search_condition_found = False
							MyGlobals.s.pop()


						for ta in range(total_added_to_solver):
							MyGlobals.s.pop()


					else:
						if debug: 
							print('\033[95m[-] In CALLDATALOAD the address does not contain symbolic variable input[*]\033[0m' )
							print( addr )
						return 

					return


				# It can be CALLDATASIZE
				elif si['o'] == 'CALLDATASIZE':


						# Assume it is SYMBOLIC variable
						storage2 = copy.deepcopy(storage)
						stack2 = copy.deepcopy(stack)
						trace2 = copy.deepcopy(trace)
						mmemory2 = copy.deepcopy(mmemory)
						data2 = copy.deepcopy(data)
						sha3_values2 = copy.deepcopy(sha3_values)
						sha3_dict2 = copy.deepcopy(sha3_dict)

						if -1 not in data2:
							data2['inputlength-'+ str(actual_key)+ '-' +function_hash] = BitVec('inputlength-'+ str(actual_key)+ '-' +function_hash, 256)
						stack2.append( {'type':'constant','step':ops[pos]['id'], 'z3': data2['inputlength-'+ str(actual_key)+ '-' +function_hash]} )

						MyGlobals.s.push()
						MyGlobals.s.append(If( data2['inputlength-'+ str(actual_key)+ '-' +function_hash] > BitVecVal(0, 256),  BitVecVal(1, 256),  BitVecVal(0, 256)) == BitVecVal(1,256) )
						
						self.execute_one_block(ops,stack2,	pos+1, 	trace2, storage2, 	mmemory2, data2, configurations,  sha3_dict2, sha3_values2, search_op, search_function,  jumpdepth, calldepth, function_hash, find_solution,  key )
						MyGlobals.s.pop()

						if search_enhance and MyGlobals.stop_search:
							return 
						MyGlobals.search_condition_found = False

						
						# or Branch on 4 different FIXED sizes
						# branch_array_size = [0,8,8+1*32,8+2*32]
						branch_array_size = [8,8+1*32,8+2*32]
						i=0
						for one_branch_size in branch_array_size:
							
							if MyGlobals.solution_found and MyGlobals.in_sha3>0 :
								return

							i+=1
							storage2 = copy.deepcopy(storage)
							stack2 = copy.deepcopy(stack)
							trace2 = copy.deepcopy(trace)
							mmemory2 = copy.deepcopy(mmemory)
							data2 = copy.deepcopy(data)
							sha3_values2 = copy.deepcopy(sha3_values)
							sha3_dict2 = copy.deepcopy(sha3_dict)
							
							stack2.append( {'type':'constant','step':ops[pos]['id'], 'z3': BitVecVal(one_branch_size,256)} )
							MyGlobals.s.push()
							
							if debug: print('\033[91m In branch %x of Calldatasize\n \033[0m'%(i))					
							self.execute_one_block(ops,stack2,	pos+1, 	trace2, storage2, 	mmemory2, data2, configurations,  sha3_dict2, sha3_values2, search_op, search_function,  jumpdepth, calldepth, function_hash, find_solution,  key )
							MyGlobals.s.pop()
							MyGlobals.search_condition_found = False
						return 

				elif si['o'] == 'SHA3':
					
					s1 = stack.pop()
					s2 = stack.pop()
					if is_fixed(s2):
						addr = get_value(s2)
					
					else:
						print('Address not fixed in sha3\n')	

					exact_address = get_value(s1) if is_bv_value(s1['z3']) else -1
					changed_offset = exact_address
					if (addr - exact_address)/32 >= 2 : changed_offset = addr/2
								
					if search_enhance:
						if not is_fixed( mmemory[changed_offset] ):
							res = {'type':'constant','step':ops[pos]['id'], 'z3': mmemory[changed_offset]['z3'] }

						else:	
							res = {'type':'constant','step':ops[pos]['id'], 'z3':BitVec('SHA3'+'-'+str(ops[pos]['id'])+'-'+function_hash, 256) }
						stack.append(res)
						newpos = pos+1
						continue
					# If the memory location of sha3 is not already defined
					if not mmemory[addr/2]['z3'].as_long() in sha3_dict:
						text = str(mmemory[get_value(s1)]['z3'])

						if 'CALLER' in str(mmemory[get_value(s1)]['z3']):

							# Find the exact name of symbolic variable.
							sm = ''
							regex = re.compile('CALLER-[0-9]-[0-9a-f]{8}')
							match = re.search( regex, text)

							if match:
								sm = text[match.start():match.end()]
							else:
								print('\033[91m[-] NO such symbolic variable found \033[0m', '\n')
								exit(0)

							# If values of the symbolic variable have already been defined
							if sm in sha3_values:
								if debug: print('In branch 1 \n')

								const_addr = sha3_values[sm][0]
								mmemory[get_value(s1)]['z3'] = BitVecVal(const_addr, 256)

								#find the keccak hash of the new concrete value
								val = '' 
								
								for i in range(addr/32):
								
									val += '%064x' % get_value(mmemory[get_value(s1) + i*32])

								k = keccak_256()
								k.update(val.decode('hex'))
								digest = k.hexdigest()
								res = {'type':'constant','step':ops[pos]['id'], 'z3':BitVecVal(int(digest,16), 256) }

								# Copy all the contents of the previous sha3 dict and sha3_values
								sha3_dict2 = copy.deepcopy(sha3_dict)
								sha3_values2 = copy.deepcopy(sha3_values)
								sha3_dict2[mmemory[addr/2]['z3'].as_long()] = []
								sha3_dict2[mmemory[addr/2]['z3'].as_long()].append(const_addr)
								# Copy all the datastructures
								storage2 = copy.deepcopy(storage)
								stack2 = copy.deepcopy(stack)
								trace2 = copy.deepcopy(trace)
								mmemory2 = copy.deepcopy(mmemory)
								data2 = copy.deepcopy(data)	 
								stack2.append( res )

								# Activate the sha3 branch
								MyGlobals.in_sha3 +=1
								MyGlobals.solution_found = False

								MyGlobals.s.push()
								self.execute_one_block(ops,stack2,	pos+1, 	trace2, storage2, 	mmemory2, data2, configurations,  sha3_dict2, sha3_values2, search_op, search_function,  jumpdepth, calldepth, function_hash, find_solution,  key )	
								MyGlobals.s.pop()
								MyGlobals.search_condition_found = False

								# Deactivate the sha3 branch
								MyGlobals.in_sha3 -= 1
								
							# If values of the symbolic variable have not been defined	
							else:
								if debug: print('In branch 2 \n')
								shuffle(MyGlobals.st['caller'])
								for each_value in MyGlobals.st['caller']:
									const_addr = long(int(each_value, 16))
									found = False
									#replace the symbolic variable with a concrete variable
									mmemory[get_value(s1)]['z3'] = BitVecVal(const_addr, 256)
									#find the keccak hash of the new concrete value
									val = '' 
									
									for i in range(addr/32):
									
										val += '%064x' % get_value(mmemory[get_value(s1) + i*32])

									k = keccak_256()
									k.update(val.decode('hex'))
									digest = k.hexdigest()
									res = {'type':'constant','step':ops[pos]['id'], 'z3':BitVecVal(int(digest,16), 256) }	
									# Copy all the contents of the previous sha3 dict and sha3_values
									sha3_dict2 = copy.deepcopy(sha3_dict)
									sha3_values2 = copy.deepcopy(sha3_values)
									sha3_dict2[mmemory[addr/2]['z3'].as_long()] = []
									sha3_dict2[mmemory[addr/2]['z3'].as_long()].append(const_addr)	
									sha3_values2[sm] = []
									sha3_values2[sm].append(const_addr)

									storage2 = copy.deepcopy(storage)
									stack2 = copy.deepcopy(stack)
									trace2 = copy.deepcopy(trace)
									mmemory2 = copy.deepcopy(mmemory)
									data2 = copy.deepcopy(data)	 
									stack2.append( res )
																	
									# Activate the sha3 branch
									MyGlobals.in_sha3 +=1
									MyGlobals.solution_found = False

									MyGlobals.s.push()
									self.execute_one_block(ops,stack2,	pos+1, 	trace2, storage2, 	mmemory2, data2, configurations,  sha3_dict2, sha3_values2, search_op, search_function,  jumpdepth, calldepth, function_hash, find_solution,  key )
									MyGlobals.s.pop()

									# Deactivate the sha3 branch
									MyGlobals.in_sha3 -= 1

									MyGlobals.search_condition_found = False

						if 'input' in str(mmemory[get_value(s1)]['z3']):

							# Find the exact name of symbolic variable.
							sm = ''
							regex = re.compile('input[0-9]*\[[0-9 ]*\]-[0-9a-f]{8}')
							match = re.search( regex, text)

							if match:
								sm = text[match.start():match.end()]
							else:
								print('\033[91m[-] No such symbolic variable found \033[0m', '\n')
								exit(0)

							# If values of the symbolic variable have already been defined	
							if sm in sha3_values:
								if debug: print('In branch 3 \n')
								const_addr = sha3_values[sm][0]
								mmemory[get_value(s1)]['z3'] = BitVecVal(const_addr, 256)

								#find the keccak hash of the new concrete value
								val = '' 
								
								for i in range(addr/32):
								
									val += '%064x' % get_value(mmemory[get_value(s1) + i*32])

								k = keccak_256()
								k.update(val.decode('hex'))
								digest = k.hexdigest()
								res = {'type':'constant','step':ops[pos]['id'], 'z3':BitVecVal(int(digest,16), 256) }

								# Copy all the contents of the previous sha3 dict and sha3_values
								sha3_dict2 = copy.deepcopy(sha3_dict)
								sha3_values2 = copy.deepcopy(sha3_values)
								sha3_dict2[mmemory[addr/2]['z3'].as_long()] = []
								sha3_dict2[mmemory[addr/2]['z3'].as_long()].append(const_addr)
								# Copy all the datastructures
								storage2 = copy.deepcopy(storage)
								stack2 = copy.deepcopy(stack)
								trace2 = copy.deepcopy(trace)
								mmemory2 = copy.deepcopy(mmemory)
								data2 = copy.deepcopy(data)	 
								stack2.append( res )

								# Activate the sha3 branch
								MyGlobals.in_sha3 +=1
								MyGlobals.solution_found = False

								MyGlobals.s.push()
								self.execute_one_block(ops,stack2,	pos+1, 	trace2, storage2, 	mmemory2, data2, configurations,  sha3_dict2, sha3_values2, search_op, search_function,  jumpdepth, calldepth, function_hash, find_solution,  key )
								MyGlobals.s.pop()
								MyGlobals.search_condition_found = False


								# Deactivate the sha3 branch
								MyGlobals.in_sha3 -= 1

							# If values of the symbolic variable have not been defined	
							else:
								if debug: print('In branch 4 \n')
								# Generate a completely random input only if key is not more than 2
								rand_input = 0

								if key<=2:
									# sha3_dict[mmemory[addr/2]['z3'].as_long()].append(long(int('%030x' % random.randrange(16**40), 16)))
									rand_input = long(int('%030x' % random.randrange(16**40), 16))

								else:
									print('\033[91m[-] Something wrong.... Asking symbolic variable for input in third call \033[0m', '\n')
									return
								lists = []
								
								for each_value in MyGlobals.st['caller']:
									lists.append(int(each_value,16))
								lists.append(rand_input)
								# shuffle(lists)	
								for value in lists:	
									const_addr = value
									found = False
									#replace the symbolic variable with a concrete variable
									mmemory[get_value(s1)]['z3'] = BitVecVal(const_addr, 256)
									#find the keccak hash of the new concrete value
									val = '' 
									
									for i in range(addr/32):
									
										val += '%064x' % get_value(mmemory[get_value(s1) + i*32])

									k = keccak_256()
									k.update(val.decode('hex'))
									digest = k.hexdigest()
									res = {'type':'constant','step':ops[pos]['id'], 'z3':BitVecVal(int(digest,16), 256) }	
									# Copy all the contents of the previous sha3 dict and sha3_values
									sha3_dict2 = copy.deepcopy(sha3_dict)
									sha3_values2 = copy.deepcopy(sha3_values)
									sha3_dict2[mmemory[addr/2]['z3'].as_long()] = []
									sha3_dict2[mmemory[addr/2]['z3'].as_long()].append(const_addr)	
									sha3_values2[sm] = []
									sha3_values2[sm].append(const_addr)

									storage2 = copy.deepcopy(storage)
									stack2 = copy.deepcopy(stack)
									trace2 = copy.deepcopy(trace)
									mmemory2 = copy.deepcopy(mmemory)
									data2 = copy.deepcopy(data)	 
									stack2.append( res )
																
									# Activate the sha3 branch
									MyGlobals.in_sha3 += 1
									MyGlobals.solution_found = False

									MyGlobals.s.push()
									self.execute_one_block(ops,stack2,	pos+1, 	trace2, storage2, 	mmemory2, data2, configurations,  sha3_dict2, sha3_values2, search_op, search_function,  jumpdepth, calldepth, function_hash, find_solution,  key )
									MyGlobals.s.pop()
									MyGlobals.search_condition_found = False


									# Deactivate the sha3 branch
									MyGlobals.in_sha3 -= 1		

							
					# If the memory location of sha3 is already defined		
					else:
						text = str(mmemory[get_value(s1)]['z3'])
						
						if 'CALLER' in str(mmemory[get_value(s1)]['z3']):

							# Find the exact name of symbolic variable.
							sm = ''
							regex = re.compile('CALLER-[0-9]-[0-9a-f]{8}')
							match = re.search( regex, text)

							if match:
								sm = text[match.start():match.end()]
							else:
								print('\033[91m[-] NO such symbolic variable found \033[0m', '\n')
								exit(0)

							# If values of the symbolic variable have already been defined
							if sm in sha3_values:
								if debug: print('In branch 5 \n')
								const_addr = sha3_values[sm][0]
								mmemory[get_value(s1)]['z3'] = BitVecVal(const_addr, 256)
								val = '' 
								
								for i in range(addr/32):
								
									val += '%064x' % get_value(mmemory[get_value(s1) + i*32])

								k = keccak_256()
								k.update(val.decode('hex'))
								digest = k.hexdigest()
								res = {'type':'constant','step':ops[pos]['id'], 'z3':BitVecVal(int(digest,16), 256) }

								sha3_dict2 = copy.deepcopy(sha3_dict)
								sha3_values2 = copy.deepcopy(sha3_values)

								# Copy all the datastructures
								storage2 = copy.deepcopy(storage)
								stack2 = copy.deepcopy(stack)
								trace2 = copy.deepcopy(trace)
								mmemory2 = copy.deepcopy(mmemory)
								data2 = copy.deepcopy(data)	 
								stack2.append( res )

								# Activate the sha3 branch
								MyGlobals.in_sha3 += 1
								MyGlobals.solution_found = False

								MyGlobals.s.push()
								self.execute_one_block(ops,stack2,	pos+1, 	trace2, storage2, 	mmemory2, data2, configurations,  sha3_dict2, sha3_values2, search_op, search_function,  jumpdepth, calldepth, function_hash, find_solution,  key )
								MyGlobals.s.pop()
								MyGlobals.search_condition_found = False

								# Deactivate the sha3 branch
								MyGlobals.in_sha3 -= 1

							# If values of the symbolic variable have not been defined	
							else:
								if debug: print('In branch 6 \n')
								const_addr = sha3_dict[mmemory[addr/2]['z3'].as_long()][0]
								const_addr = convert_int_to_hexStr(const_addr)

								if const_addr in MyGlobals.st['caller']:
									const_addr = convert_hexStr_to_int(const_addr)
									#replace the symbolic variable with a concrete variable
									mmemory[get_value(s1)]['z3'] = BitVecVal(const_addr, 256)
									#find the keccak hash of the new concrete value
									val = '' 
									
									for i in range(addr/32):
									
										val += '%064x' % get_value(mmemory[get_value(s1) + i*32])

									k = keccak_256()
									k.update(val.decode('hex'))
									digest = k.hexdigest()
									res = {'type':'constant','step':ops[pos]['id'], 'z3':BitVecVal(int(digest,16), 256) }	
									# Copy all the contents of the previous sha3 dict and sha3_values
									sha3_dict2 = copy.deepcopy(sha3_dict)
									sha3_values2 = copy.deepcopy(sha3_values)
									sha3_dict2[mmemory[addr/2]['z3'].as_long()] = []
									sha3_dict2[mmemory[addr/2]['z3'].as_long()].append(const_addr)	
									sha3_values2[sm] = []
									sha3_values2[sm].append(const_addr)

									storage2 = copy.deepcopy(storage)
									stack2 = copy.deepcopy(stack)
									trace2 = copy.deepcopy(trace)
									mmemory2 = copy.deepcopy(mmemory)
									data2 = copy.deepcopy(data)	 
									stack2.append( res )
																	
									# Activate the sha3 branch
									MyGlobals.in_sha3 += 1
									MyGlobals.solution_found = False

									MyGlobals.s.push()
									self.execute_one_block(ops,stack2,	pos+1, 	trace2, storage2, 	mmemory2, data2, configurations,  sha3_dict2, sha3_values2, search_op, search_function,  jumpdepth, calldepth, function_hash, find_solution,  key )
									MyGlobals.s.pop()
									MyGlobals.search_condition_found = False

									# Deactivate the sha3 branch
									MyGlobals.in_sha3 -= 1

								else:
									print('\033[91m[-] The symbolic variable caller cannot take this value \033[0m')
									return 				

						if 'input' in str(mmemory[get_value(s1)]['z3']):

							# Find the exact name of symbolic variable.
							sm = ''
							regex = re.compile('input[0-9]*\[[0-9 ]*\]-[0-9a-f]{8}')
							match = re.search( regex, text)

							if match:
								sm = text[match.start():match.end()]
							else:
								print('\033[91m[-] No such symbolic variable found \033[0m', '\n')
								exit(0)

							# If values of the symbolic variable have already been defined	
							if sm in sha3_values:
								if debug: print('In branch 7 \n')
								const_addr = sha3_values[sm][0]
								mmemory[get_value(s1)]['z3'] = BitVecVal(const_addr, 256)

								#find the keccak hash of the new concrete value
								val = '' 
								
								for i in range(addr/32):
								
									val += '%064x' % get_value(mmemory[get_value(s1) + i*32])

								k = keccak_256()
								k.update(val.decode('hex'))
								digest = k.hexdigest()
								res = {'type':'constant','step':ops[pos]['id'], 'z3':BitVecVal(int(digest,16), 256) }

								# Copy all the contents of the previous sha3 dict and sha3_values
								sha3_dict2 = copy.deepcopy(sha3_dict)
								sha3_values2 = copy.deepcopy(sha3_values)
								
								# Copy all the datastructures
								storage2 = copy.deepcopy(storage)
								stack2 = copy.deepcopy(stack)
								trace2 = copy.deepcopy(trace)
								mmemory2 = copy.deepcopy(mmemory)
								data2 = copy.deepcopy(data)	 
								stack2.append( res )

								# Activate the sha3 branch
								MyGlobals.in_sha3 += 1
								MyGlobals.solution_found = False

								MyGlobals.s.push()
								self.execute_one_block(ops,stack2,	pos+1, 	trace2, storage2, 	mmemory2, data2, configurations,  sha3_dict2, sha3_values2, search_op, search_function,  jumpdepth, calldepth, function_hash, find_solution,  key )
								MyGlobals.s.pop()
								MyGlobals.search_condition_found = False

								# Deactivate the sha3 branch
								MyGlobals.in_sha3 -= 1

							# If values of the symbolic variable have not been defined	
							else:
								if debug: print('In branch 8 \n')
								# Generate a completely random input only if key is not more than 2
								rand_input = 0

								if key<=2:
									rand_input = long(int('%030x' % random.randrange(16**40), 16))

								else:
									print('\033[91m[-] Something wrong.... Asking symbolic variable for input in third call \033[0m', '\n')
									return
								
								lists = []
								lists.append(rand_input)
								lists.append(sha3_dict[mmemory[addr/2]['z3'].as_long()][0])
								

								for each_value in lists:
									const_addr = each_value
									#replace the symbolic variable with a concrete variable
									mmemory[get_value(s1)]['z3'] = BitVecVal(const_addr, 256)
									#find the keccak hash of the new concrete value
									val = '' 
									
									for i in range(addr/32):
									
										val += '%064x' % get_value(mmemory[get_value(s1) + i*32])

									k = keccak_256()
									k.update(val.decode('hex'))
									digest = k.hexdigest()
									res = {'type':'constant','step':ops[pos]['id'], 'z3':BitVecVal(int(digest,16), 256) }	
									# Copy all the contents of the previous sha3 dict and sha3_values
									sha3_dict2 = copy.deepcopy(sha3_dict)
									sha3_values2 = copy.deepcopy(sha3_values)
									sha3_values2[sm] = []
									sha3_values2[sm].append(const_addr)

									storage2 = copy.deepcopy(storage)
									stack2 = copy.deepcopy(stack)
									trace2 = copy.deepcopy(trace)
									mmemory2 = copy.deepcopy(mmemory)
									data2 = copy.deepcopy(data)	 
									stack2.append( res )
																	
									# Activate the sha3 branch
									MyGlobals.in_sha3 += 1
									MyGlobals.solution_found = False

									MyGlobals.s.push()
									self.execute_one_block(ops,stack2,	pos+1, 	trace2, storage2, 	mmemory2, data2, configurations,  sha3_dict2, sha3_values2, search_op, search_function,  jumpdepth, calldepth, function_hash, find_solution,  key )
									MyGlobals.s.pop()
									MyGlobals.search_condition_found = False	

									# Deactivate the sha3 branch
									MyGlobals.in_sha3 -= 1				
					

					if MyGlobals.in_sha3 == 0:
						MyGlobals.solution_found = False		
					return

				# If nothing from above then stop
				else:
					print('\033[95m[-] Unknown %s on line %x \033[0m' % (si['o'],ops[pos]['id']) )
					return 

