from __future__ import print_function
from values import MyGlobals
from hashlib import *
from z3 import *
from sha3 import *
import opcodes
import script
import json
import execute_instruction
import datetime
import sqlite3
import subprocess
import shlex
import re
import time

''' 
Debug API: All the print functions below are used for pretty-printing/debugginga
'''

# Print execution stack during runtime.
def print_stack(stack):
	print('\033[90m------------------------------------- STACK -------------------------------------')
	for s in stack[::-1]:
		if 'z3' in s:
			if is_bv_value( simplify(s['z3'])): print('%10s : %4x  : %x' % (s['type'],s['step'],simplify(s['z3']).as_long() ) )
			else: print('%10s : %4x  : %s' % (s['type'],s['step'], simplify(s['z3']) ) )
		else:
			print('%10s : %4x  ' % (s['type'],s['step']) )
	print('\033[0m')

# Print global storage of the contract during runtime
def print_storage(storage):
	print('************************************ STORAGE ************************************')
	for fl in storage:
		for s in storage[fl]:
			print('\033[91m[ %64x ] \033[0m : ' % (fl), end='' )        
			if is_bv_value( simplify(s['z3'])): print('%x' % (simplify(s['z3']).as_long() ) )
			else: print('%s' % (simplify(s['z3']) ) )

# Print memory of the contract during runtime.
def print_memory(mmemory):
	print('************************************ MEMORY ************************************')
	for m in mmemory:
		fl = mmemory[m]
		print('\033[91m[ %64x ] \033[0m : ' % (m), end='' )        
		if execute_instruction.is_undefined(fl): print('undefined' )
		elif is_bv_value( simplify(fl['z3'])): print('%x' % (simplify(fl['z3']).as_long() ) )
		else: print('%s' % (simplify(fl['z3']) ) )            

# Print sha3_dict which is used in SHA3 opcode implementation. (Debugging purpose)		
def print_sha3(sha3_dict):
	print('************************************ SHA3 addresses ************************************')
	for m in sha3_dict:
		fl = sha3_dict[m]
		print('\033[91m[ %64x ] \033[0m : ' % (m), end='' )        
		for each in fl:
			if isinstance(each, int):
				print(hex(each).rstrip('L').lstrip('0x') + ' ,')
			
# Print sha3_values which is used in SHA3 opcode implementation. (Debugging purpose)		
def print_sha3_values(sha3_values):
	print('************************************ SHA3 concrete values ************************************')
	for m in sha3_values:
		fl = sha3_values[m]
		print('\033[91m[ %64s ] \033[0m : ' % (m), end='' )        
		for each in fl:
			print(hex(each).rstrip('L').lstrip('0x') + ' ,')

# Print the execution trace.
def print_trace(trace):

	print('++++++++++++++++++++++++++++ Trace ++++++++++++++++++++++++++++')
	for o in trace:
		print('%6x  : %2s : %12s : %s' % (o['id'],o['op'],o['o'] , o['input']) )

# Print contract function names.
def print_function_name(funclist, f=False):
	if not f:
		print('++++++++++++++++++++++++++++ Functions List ++++++++++++++++++++++++++++')
		for function_name, funchash in funclist:
			print('%s %30s : %8s' % (function_name, '\t', funchash) )   

	else:
		f.write('++++++++++++++++++++++++++++ Functions List ++++++++++++++++++++++++++++'+'\n')
		for function_name, funchash in funclist:
			f.write('%s %30s : %8s' % (function_name, '\t', funchash) + '\n')           

# Print the final solution in the raw form {(symbolic variable, value),}
def print_solution(function1, function2, fn1, fn2, sol_dict):

	print('\033[92m ******************* HB: %s , %s : %s , %s  \033[92m *******************\033[0m' % (fn1, fn2, function1, function2))
	
	for key, mydict in sol_dict.items():

		print('\033[93mSolution %s : \033[0m'%(str(key)))
		for each, value in mydict.items():
			print('\nContext for \033[92m %s \033[0m'%(str(each)))

			for lists in value:
				print('%-20s : %s' % (lists[0],str(lists[1])) )

# Print the final nodes output by static analysis.
def print_nodes(nodes, f = False):
	if not f:
		print('++++++++++++++++++++++++++++ Final Nodes ++++++++++++++++++++++++++++')
		for index, node in nodes.items():
		# for node in nodes:
			for func, ctx in node.items():
				print('\033[1m %s : %s \n \033[0m'%(str(index), func))
				for (key, value) in ctx:
					if isinstance(value, int):
						value = hex(value).rstrip('L').lstrip('0x')
					print(key, '%10s'%('\t'), '------->', value, '\n')

	else:
		f.write('++++++++++++++++++++++++++++ Final Nodes ++++++++++++++++++++++++++++'+'\n')
		for index, node in nodes.items():
		# for node in nodes:
			for func, ctx in node.items():
				f.write('%s : %s \n'%(str(index), func)+'\n')
				for (key, value) in ctx:
					if isinstance(value, int):
						value = hex(value).rstrip('L').lstrip('0x')
					f.write(key + '%10s'%('\t')+ ' -------> ' + value + '\n')

# Print the final nodes output by static analysis. (just a variant of previous method used to extract final nodes from a list instead of a dictionary)
def print_nodes_list(nodes, f = False):
	if not f:
		print('++++++++++++++++++++++++++++ Final Nodes ++++++++++++++++++++++++++++')
		index = 0
		for node in nodes:
		# for node in nodes:
			print('\033[1m\n%s : %s  \033[0m'%(str(index), node['name']))
			for key, value in node.items():
				if not key == 'name':
					if isinstance(value, int):
						value = hex(value).rstrip('L').lstrip('0x')
					print('%-15s -------> %s' %(key, value) )
			index+=1		

	else:
		f.write('++++++++++++++++++++++++++++ Final Nodes ++++++++++++++++++++++++++++'+'\n')
		for node in nodes:

			f.write('%s : %s \n'%(str(index), node['name'])+'\n')
			for key, value in node.items():
				if not key == 'name':
					if isinstance(value, int):
						value = hex(value).rstrip('L').lstrip('0x')
					f.write(key + '%10s'%('\t')+ ' -------> ' + value + '\n')	

# Print if an instruction has not been implemented.
def print_notimplemented():
	for key, value in MyGlobals.notimplemented_ins.items():
		print(key + ' :: ' + str(value))			

# Used for debugging purposes.
def safe_subprocess(a1, a2, max_tries, wait_time):

	FNULL = open(os.devnull, 'w')
	try_no = 0
	while True:
		try:
			solc_p = subprocess.Popen(shlex.split(a1 % a2), stdout = subprocess.PIPE, stderr=FNULL)
		except Exception as e:
			print('Exception:', e)
			time.sleep(wait_time)
			try_no +=1
			if try_no >= max_tries:
				print('Cannot pass the exception')
				print('Called subprocess with args:',a1,a2)
				exit(1)
			continue
		break

	return solc_p


'''
Debug API ends.......
'''


'''
Helper functions 
'''

# converts a hexadecimal string to integer.
def convert_hexStr_to_int(hexStr):
	longNum = 0
	if isinstance(hexStr, str):
		longNum = int(hexStr, 16)
	
	return	int(longNum)

# converts an integer into a hexadecimal string.
def convert_int_to_hexStr(number):
	hexStr = ''
	if not isinstance(number, str):
		hexStr += hex(number)

	return hexStr.lstrip('0x').rstrip('L')	

# remove the 0x from the string.
def remove0x(string):
	if string[0:2] == '0x':
		string = string[2:]
	
	return string

# This function is used to find blockumber from which the initial contract state has to be chosen.
# by default the state is taken from the blocknumber right after contract creation. If the variable owner_last 
# is set then the state is taken from blocknumber after all the initialization done by owner after conntract creation.
def find_blockNumber(contract_address, owner_last = False):
	dbcon = sqlite3.connect('/mnt/d/mnt_c/contract-main.db')

	# find the owner and contract creation block
	c_details = dbcon.execute('select creator, block from contracts where address='+'"%s"'%(contract_address))
	owner = ''
	c_blocknumber = 0

	for each in c_details:
		owner = each[0]
		c_blocknumber = each[1]

	last_block = c_blocknumber+1
	if owner_last:
		# Find the blocknember of the last owner transaction after creation.
		tx_details = dbcon.execute('select txfrom, block from tx where txto='+ '"%s"'%(contract_address) + ' order by block')

		for each_tx in tx_details:

			if owner == each_tx[0]:
				if each_tx[1] >= last_block: last_block = each_tx[1]
			else:
				break	

	return last_block+1		

# convert the solidity code into bytecode and then produce hashes
def getFuncHashes(sol_file, debug):

	solc_cmd = "solc --optimize --bin-runtime %s"
	solc_cmd1 = 'solc --hashes %s'
	FNULL = open(os.devnull, 'w')
	max_size = -1
	max_code = ''
	max_cname = ''
	
	# handle execption
	max_no_tries = 100
	try_no = 0
	solc_p = safe_subprocess ( solc_cmd , sol_file , 100, 1 )
	solc_out = solc_p.communicate()


	if debug: print(solc_out)


	for (cname, bin_str) in re.findall(r"\n======= (.*?) =======\nBinary of the runtime part: \n(.*?)\n", solc_out[0].decode('utf-8')):
		if len(bin_str)>max_size:
			max_size = len(bin_str)
			max_code = bin_str
			max_cname = cname

	funclist = []        

	try_no = 0
	solc_p1 = safe_subprocess( solc_cmd1 , sol_file, 100, 1 )
	solc_out1 = solc_p1.communicate()
	solc_str = solc_out1[0].decode('utf-8').lstrip('\n').rstrip('\n')

	if not solc_str=='':
		pass
	else:
		print('No solidity code in file\n')    				


	#
	# Get function names and  corresponding hashes with regular expression
	#
	hs = re.findall(r'^[a-fA-F0-9]{8}: .*\)', solc_str, flags=re.MULTILINE)
	for h in hs:
		ars = h.split(':')
		ars[0] = ars[0].replace(' ','')
		ars[1] = ars[1].replace(' ','')
		funclist.append( [ars[1],ars[0]])
	

	if debug: print(funclist)
	return funclist

# Computes hash of input
def get_hash(txt):
	k = md5()
	k.update(txt.encode('utf-8'))
	return int(k.hexdigest(),16)

# get the function hashes heuristically instead of using any solidity API.
def get_func_hashes(binfile):

	complete_disasm = script.disasm(binfile, 0)

	disasm = []

	for key, value in complete_disasm.items():
		disasm  = value[0]

	funclist = []
	for i in range(0, len(disasm)-4):
		if(disasm[i][1]=='PUSH4'):
			hexc = disasm[i][-1]
			if(disasm[i+2][1]=='EQ'):
				if('PUSH' in disasm[i+3][1]):
					if('JUMPI'==disasm[i+4][1]):
						funclist.append([i, hexc])
			elif(disasm[i+1][1]=='EQ'):
				if('PUSH' in disasm[i+2][1]):
					if('JUMPI'==disasm[i+3][1]):
						funclist.append([i-1, hexc])
	return funclist		

# returns True wohen a solution should be accepted. This function filters out the duplicate and unwanted solutions.
def solution_filter(solution, function1, function2):
	keys = []
	for key, value in solution.items():
		if 'inputlength' in key:
			keys.append(key)
		
	for each_key in keys:
		solution.pop(each_key, None)

	if not solution in MyGlobals.solution_dict[(function1, function2)] and len(MyGlobals.solution_dict[(function1, function2)]) < MyGlobals.max_solutions:

		if len(MyGlobals.solution_dict[(function1, function2)]) ==  MyGlobals.max_solutions-1:
			found = False
			
			for lists in MyGlobals.solution_dict[(function1, function2)]:
				for key, value in lists.items():
					if 'CALLER' in key:
						if key in solution:
							if solution[key] == value and value in MyGlobals.st['caller']: 
								found = True
								break
			if found: return False

		return True

	return False					

# Determines the TX inputs i.e., solves the symbolic constraints to give solutions of nodes.
def get_function_calls( calldepth, key, function_hash, function1, function2, debug ):

	global s, d, no_function_calls, function_calls

	MyGlobals.num_solver_calls+=1
	time1 = datetime.datetime.now()	

	temp_solver = Solver()
	if key ==1:
		temp_solver.add(MyGlobals.s.assertions())

	if key == 3:
		temp_solver.add(MyGlobals.s1.assertions())
		temp_solver.add(MyGlobals.s.assertions())

	elif key == 4:
		temp_solver.add(MyGlobals.s2.assertions())
		temp_solver.add(MyGlobals.s.assertions())	
	
	satisfied = False	
	if temp_solver in MyGlobals.solver_configurations:
		satisfied = MyGlobals.solver_configurations[temp_solver]
		temp_solver.check()
		print('found solution1')

	else:
		if temp_solver.check() == sat:
			satisfied = True
			MyGlobals.solver_configurations[temp_solver] = satisfied

		else:
			satisfied = False
			MyGlobals.solver_configurations[temp_solver] = satisfied		

	if satisfied:
		time2 = datetime.datetime.now()
		MyGlobals.total_time_solver+=(time2-time1).total_seconds()
		m = temp_solver.model()

		if debug: print('\nSolution:')
		sol = {}
		for d in m:
			if debug: print('%s -> %x' % (d,m[d].as_long() ) )
			sol[str(d)] = '%x' % m[d].as_long()

		# Extracting the function inputs
		function_inputs = {}
		functionarr = [function1, function2]
		# Get separate calldepth inputs
		if debug: print(sol)

		for cd in range(1,3):
			function_hash = functionarr[cd-1]
			if not function_hash == 'noHB':
				# Find next free
				next_free = 0
				for f in range(100):
					if ('input'+str(cd)+'['+str(4+32*f)+']'+'-'+function_hash) in sol or ('input'+str(cd)+'['+str(4+32*f)+']'+'-'+function_hash+'d') in sol:
						next_free = 32*f + 32

				# Fix weird addresses
				for f in range(100):
					addr = 'input'+str(cd)+'['+str(4+32*f)+']'+'-'+ function_hash+'d'
					if addr in sol:
						old_address = int(sol[addr],16)  
						del sol[addr]
						sol[addr[:-1]] =  '%x'% next_free

						for offset in range(100):
							check_address = 'input'+str(cd)+'['+('%x'%(4+old_address + 32*offset))+']' + '-'+function_hash
							if check_address in sol:
								sol['input'+str(cd)+'['+'%d'%(4+int(next_free)) +']' +'-'+ function_hash] = sol[check_address]
								del sol[check_address]
								next_free += 32


				# Produce the input of the call
				tmp_one = {}
				for addr in sol:
					if addr.find('input'+str(cd)+'[') >= 0:
						tmp_one[addr] = sol[addr]

				# Function arguments
				max_seen = 4
				function_inputs[cd] = function_hash
				for offset in range(100):
					addr = 'input'+str(cd)+'['+'%d'%(4+offset*32)+']' + '-' + function_hash
					if addr in tmp_one:
						function_inputs[cd] = function_inputs[cd] + '%064x' % int(tmp_one[addr],16)
						max_seen = 4+(offset+1)*32
						del tmp_one[addr]
					else:
						function_inputs[cd] = function_inputs[cd] + '%064x' % 0

				function_inputs[cd] = function_inputs[cd][:2*max_seen]

				if len(tmp_one) > 0:
					print('Some addresses are larger')
					print(tmp_one)
					return False

		for num in range(1, 3):
			if num ==1:
				sol['input'+'-'+function1] = function_inputs[num]	
			if num ==2:				
				if not function2 == 'noHB':
					sol['input'+'-'+function2] = function_inputs[num]

		return sol
	


	else:
		time2 = datetime.datetime.now()
		MyGlobals.total_time_solver+=(time2-time1).total_seconds()
		return False


