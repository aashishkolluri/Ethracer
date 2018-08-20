from __future__ import print_function
from sys import *
from op_list import *
from op_parse import *
from op_exec import get_storage_value, get_params, set_params, clear_params, print_stack, print_storage, execute, print_balances, get_balances, same_balance, send_ether, st
from op_exec import print_balance_difference, save_state, same_state 
import glob
import os
import time
import sys
import copy
import itertools
import random
import re
import datetime

bugtypes = [{},{}]
minimal_found_traces = [[],[]]
all_traces = [[],[]]
sall_traces = [[],[]]
ah = {}
temp_storage = {}

MAX_LEN_MINIMAL_FOUND_TRACES = 100
MAX_LEN_ALL_TRACES           = 100000
ONE_CONTRACT_fuzzer_TIMEOUT = 30 * 60

PATH_REPORTS = 'reports/'

global st


def add_bug(ls, criteria):
	v = 0
	for l in ls:
		v += 1<<l

	if v in bugtypes[criteria]: 
		bugtypes[criteria][v] += 1
	else: 
		bugtypes[criteria][v] = 1



def analyze_bugs( nodes , criteria, onlyprint = True ):

	dbt =[]
	for b in bugtypes[criteria]:
		l = []
		for i in range(10):
			if (b>>i)&1 : 
				l.append(nodes[i]['name'])
		if len(l) > 0:
			found = False
			for el in dbt:
				if el[0] == l:
					el[1] += bugtypes[criteria][b]
					found = True
					break
			if not found:
				dbt.append( [l, bugtypes[criteria][b] ] )


	dbt.sort(key=lambda x: x[1], reverse=True )

	if onlyprint:
		print('Bug types: %d' % len(dbt))
		first = True
		for bg in dbt:
			if first:
				print('-'*60)
				first = False
			print('%3d : ' % bg[1], end = '')
			print(bg[0])
	else:
		return dbt



def execute_one_function( contract_address, code , tx_caller, tx_input, tx_value, storage, debug, st_blocknumber, read_from_blockchain = False):
	global temp_storage

	stack   = []
	mmemory = {}
	data = {}

	set_params('call_data_size','',len(tx_input))
	set_params('call_data_load','',tx_input)
	set_params('call_value','',tx_value)
	set_params('caller','',tx_caller)
	set_params('origin','',tx_caller)
	
	if not send_ether( hex(tx_caller).rstrip('L').lstrip('0x'), contract_address.lstrip('0x'), tx_value):
		print('Cannot execute function because the caller does not have enough Ether')
		return False
	
	# Execute the next block of operations
	first = True
	pos = 0
	newpos = pos
	
	while (first or newpos != pos):

		first = False
		pos = newpos    
					
		# If no more code, then stop
		if pos >= len(code) or pos < 0:
			if debug:
				print('\033[94m[+] Reached bad/end of execution\033[0m')
				print_stack( stack )
			return False

		if debug: print('%3x : %16s : %s' % (code[pos]['id'], code[pos]['o'], code[pos]['input']) )

	
		# Check if the current op is one of the stop code
		if code[pos]['o'] == 'STOP' or code[pos]['o'] == 'RETURN' :
			return True

		# Execute the next instruction
		stack, newpos, ret, mmemory = execute( code, stack, pos, storage, temp_storage, mmemory, data,  st_blocknumber, debug, read_from_blockchain  )

#       print_stack(stack)
		

		# If it returned True, it means the execution should halt
		if ret: 
			if debug: print('Reached halt statement on %3x : %16s : %s' % (code[pos]['id'], code[pos]['o'], code[pos]['input']) )
			return False
	
		# If program counter did not move then 
		if pos == newpos:
			print('\033[95m[-] Unknown %s on line %x \033[0m' % (si['o'],code[pos]['id']) )
			exit(1)
			return False

	



def check_one_trace( contract_address, trace, storage, code, debug, read_from_blockchain, st_blocknumber):

	# Each function in the trace is defined by
	# name - the name of the functions
	# tx_input  - input data (include function hash)
	# tx_caller - sender 
	# tx_value  - msg.value
	# params - set of parameters that should be set (usually block number, etc)
	# each is defined with:
	#   0 - parameter
	#   1 - input
	#   2 - value

	e = True
	#extra params that could vary for every node
	blocknumber  = 0
	timestamp = 0
	blockhash = 0

	for t in trace:
		if 'tx_blocknumber' in t:
			blocknumber = int(t['tx_blocknumber'], 16)

		if 'tx_timestamp' in t:
			timestamp = int(t['tx_timestamp'], 16)

		if 'tx_blockhash' in t:
			blockhash = t['tx_blockhash']

		if not 'tx_value' in t:
			t['tx_value'] = 0

		set_params('blocknumber', '', blocknumber)
		set_params('timestamp', '', timestamp)
		set_params('blockhash', '', blockhash)

		tx_value = t['tx_value']
		if isinstance(tx_value, str):
			tx_value = int(tx_value, 16)

		tx_caller  =    int(t['tx_caller'], 16)
		# contract_address_hex = hex(int(contract_address,16)+0x200)[2:]
		# print(t)
		# # Set the parameters
		# for par in t['params']:
		#   set_params( par[0] , par[1] , par[2] )

		# Set storage
		if 'storage' in t:
			for st in t['storage']:
				if st[0] == 'bool':
					addr = st[1]
					index= st[2]
					value= st[3]
					fullvalue = get_storage_value( '0x%040x' % contract_address, addr, st_blocknumber, read_from_blockchain)
					if fullvalue[0:2] == '0x': fullvalue = fullvalue[2:]
					fullvalue = int(fullvalue,16)
					newvalue  = (fullvalue & ( (2**256 - 1) ^ (0xff<<(8*index)))) ^ (value << (8*index))
					storage[ addr ] = newvalue
					# temp_storage[addr] = newvalue

		e = e and execute_one_function( contract_address, code , tx_caller, t['tx_input'], tx_value, storage, debug, st_blocknumber, read_from_blockchain )
		if not e: return False

	return True


def print_trace(trace, f= False):
	if not f:
		print('------------------------------------------')
	else:
		print('------------------------------------------\n')

	for t in trace:
		if not f:
			print('%25s  :  %40x : %s' % (t['name'], int(t['tx_caller'], 16),t['tx_input']) )
		else:
			f.write('%25s  :  %40x : %s' % (t['name'], int(t['tx_caller'], 16),t['tx_input']) + '\n')   
	if not f:
		print('------------------------------------------')
	else:
		print('------------------------------------------\n')   

def follows_hb( trace, hb ):
	for i in range(len(trace)):
		for j in range(i+1,len(trace)):
			if (trace[j],trace[i]) in hb: return False
	return True

def is_good_trace(trace, hb, nodes):

	# Check the trace satisfies HB and see that each node in the trace has higher timestamp and blocknumber than all its predecessors.
	for i in range(len(trace)):
		for j in range(i+1, len(trace)):
			if (trace[j], trace[i]) in hb: return False

			if 'tx_timestamp' in nodes[trace[j]] and 'tx_timestamp' in nodes[trace[i]]: 
				if int(nodes[trace[j]]['tx_timestamp'], 16) < int(nodes[trace[i]]['tx_timestamp'],16): return False
			if 'tx_blocknumber' in nodes[trace[j]] and 'tx_blocknumber' in nodes[trace[i]]: 
				if int(nodes[trace[j]]['tx_blocknumber'],16) < int(nodes[trace[i]]['tx_blocknumber'],16): return False
	return True

def set_balances(trace, contract_address, nodes):

	# For all the users in the trace we give an initial equal balance of 10**22 and 
	# for the contract we give the max balance encountered any of the nodes of that trace.
	max_balance = -1
	default_addr = '7'*40

	for index in trace:
		# print(nodes[index], index)
		if 'tx_caller' in nodes[index]:
			# print('I am here\n')
			set_params('balance', nodes[index]['tx_caller'], 10**22)
		else:
			nodes[index]['tx_caller'] = default_addr
			set_params('balance', default_addr, 10**22)

		if 'tx_balance' in nodes[index]:
			if nodes[index]['tx_balance'] > max_balance:
				max_balance = nodes[index]['tx_balance']

	if max_balance == -1:
		max_balance = 10**18

	set_params('balance', contract_address, max_balance)

def is_really_new_trace(  new_trace, criteria ):

	(a,b) = new_trace


	# If trace already seen then it is not new
	if (a,b) in minimal_found_traces[criteria] or (b,a) in minimal_found_traces[criteria]: 
		return False

	# If the trace has length at most 2 then no need to further analyze, it is new
	if len(a) <= 2:
		return True


	# Remove one element from the trace pair and check recursively if it is new
	tnew = True
	for i in range(len(a)):
		for j in range(len(b)):
			if a[i] == b[j]:
				ct = copy.deepcopy(new_trace)
				del ct[0][i]
				del ct[1][j]
				tnew = tnew and is_really_new_trace( ct, criteria )

	return tnew

def check_one_depth_all_traces( depth, nodes, hb, storage_predefined, balances, contract_address, contract_bytecode, code, criteria, debug, read_from_blockchain, st_blocknumber, time1, par):
	
	print('*'*80+'\n' +'*'*80+ '\nDepth: %d' % depth)

	n = range(len(nodes))
	all_possible_traces = list(itertools.combinations(n, depth))

	total_traces = 0
	hb_passed_traces = 0

	count = 0
	for one_trace in all_possible_traces:

		# Return if fuzzer takes more time than expected
		time2 = datetime.datetime.now()
		#print('Time is ', time2)
		if ONE_CONTRACT_fuzzer_TIMEOUT < int((time2 - time1).total_seconds()):
			return -1 , -1

		count +=1
		print('\rCheck:  %5d out of %5d traces       ' % (count, len(all_possible_traces)), end='')
		sys.stdout.flush()

		all_storages = {}
		all_balances = {}
		all_states  = {}
		permuted_traces = itertools.permutations(one_trace, len(one_trace))
		for new_trace in permuted_traces:

			total_traces +=1

			# Check on HB relation
			if not is_good_trace( new_trace, hb, nodes): continue
			hb_passed_traces +=1

			# Construct the trace
			full_trace = [nodes[j] for j in new_trace]

			# Execute the trace
			storage = {}
			clear_params()
			set_params('contract_address','',contract_address )
			set_balances(new_trace, contract_address.lstrip('0x'), nodes)

			ct = check_one_trace( contract_address, full_trace, storage, code, debug, read_from_blockchain, st_blocknumber )
			if ct:
				all_storages[new_trace] = copy.deepcopy( storage )
				all_balances[new_trace] = copy.deepcopy( get_balances() )


		for i in all_storages:
			for j in all_storages:

				# Do not consider traces with permutations of the same function
				if True:
					diff_func = {}
					for z in i:
						diff_func[nodes[z]['name']] = True

					skip = False
					for df in diff_func:
						tr1 = []
						tr2 = []
						for z in i:
							if nodes[z]['name'] == df:
								tr1.append(z)
						for z in j:
							if nodes[z]['name'] == df:
								tr2.append(z)

						if tr1 != tr2:
							skip = True

					if skip: continue


				
				for zz in range(2):

				   if 0==zz and not same_state(all_storages[i], all_storages[j]) \
					  or \
					  1==zz and not same_balance(all_balances[i], all_balances[j]):

						 # Check if similar trace has already been seen
						t1 = []
						t2 = []
						for t in range(len(i)):
							t1.append( ah[nodes[i[t]]['name']])
							t2.append( ah[nodes[j[t]]['name']])
						if (t1,t2) in sall_traces[zz] or (t2,t1) in sall_traces[zz]: continue
						sall_traces[zz].append((t1,t2))


						if len(all_traces[zz]) < MAX_LEN_ALL_TRACES:
							if (i,j) not in all_traces[zz] and (j,i) not in all_traces[zz]:
								all_traces[zz].append((i,j))

						# Minimal traces
						if len(minimal_found_traces[zz])< MAX_LEN_MINIMAL_FOUND_TRACES:
							tr1 = [nodes[s]['name'] for s in i]
							tr2 = [nodes[s]['name'] for s in j]
							if is_really_new_trace( (tr1,tr2), 0 ):
								minimal_found_traces[zz].append( (tr1,tr2) )

						# Bug types
						involved = []
						for z in range(len(i)):
							if i[z] != j[z] and i[z] not in involved:
								involved.append(i[z])
						add_bug ( involved , zz )

			


	print('\n\nTraces  HB passed / total : %6d /  %6d' % (hb_passed_traces, total_traces) )

	for zz in range(2):

		print('\n'+'='*30+' '+('Storage' if 0==zz else 'Balance') + ' equality '+'='*30)
		print('Minimal found traces: %d ' % len(minimal_found_traces[zz]))
		for ft in minimal_found_traces[zz]:
			print('-'*60)
			print('\t', ft[0] )
			print('\t', ft[1] )
		print()

		analyze_bugs( nodes, zz )    

		print('\nFull traces: %d' % len(all_traces[zz]))

	
	'''
	print('\n'+'='*30+' Balance equality '+'='*30)
	print('Minimal found traces: %d ' % len(minimal_found_traces[1]))
	for ft in minimal_found_traces[1]:
		print('-'*60)
		print('\t', ft[0] )
		print('\t', ft[1] )
	print()

	analyze_bugs( nodes, 1 )  
	'''


	return hb_passed_traces, total_traces



def check_all_traces( trace, max_depth, nodes, hb, storage_predefined, balances, contract_address, contract_bytecode, code, criteria, debug, read_from_blockchain, st_blocknumber, time1, par):
	temp_storage.clear()

	max_depth = 6


	global bugtypes, minimal_found_traces, all_traces, sall_traces, ah

	bugtypes = [{},{}]
	minimal_found_traces = [[],[]]
	all_traces = [[],[]]
	sall_traces = [[],[]]
	ah = {}

	# remove function parameters
	for n in nodes: 
		n['name'] = re.sub(r'\((.)*\)', '', n['name'])

	cnt = 0
	for n in nodes:
		if n['name'] not in ah:
			ah[n['name']] = cnt
			cnt +=1 

	chb = 0
	ctot= 0
	for i in range(2,max_depth+1):
		thb,ttot = check_one_depth_all_traces( i, nodes, hb, storage_predefined, balances, contract_address, contract_bytecode, code, criteria, debug, read_from_blockchain, st_blocknumber, time1,par)
		if thb == -1 and ttot == -1:
			break
		chb += thb
		ctot+= ttot

	print('\n\nTotal traces  HB passed / total : %6d /  %6d' % (chb, ctot) )

	rp = dict()
	rp[0] = 'storage'
	rp[1] = 'balance'

	# Minimal traces
	for k in rp:
		with open(PATH_REPORTS+contract_address+'-'+rp[k]+'-minimal.txt','w') as f:
			f.write('Minimal found traces: %d \n' % len(minimal_found_traces[k]))
			for ft in minimal_found_traces[k]:
				f.write('-'*80+'\n')
				f.write(str(ft[0]) + '\n' )
				f.write(str(ft[1]) + '\n' )
			f.close()

	# Bugtypes
	for k in rp:
		with open(PATH_REPORTS+contract_address+'-'+rp[k]+'-types.txt','w') as f:
			dbt = analyze_bugs( nodes, k , False )
			f.write('Bug types: %d\n' % len(dbt))
			first = True
			for bg in dbt:
				if first:
					f.write('-'*80+'\n')
					first = False
				f.write('%3d : ' % bg[1])
				f.write(str(bg[0]))
				f.write('\n')

			f.close()


	# Full buggy traces
	for k in rp:
		with open(PATH_REPORTS+contract_address+'-'+rp[k]+'-all.txt','w') as f:
			f.write('Nodes\n'+'-'*80+'\n')
			for n in range(len(nodes)):
				f.write(str(n)+' : '+ str(nodes[n])+'\n')
			f.write('-'*80+'\n\n')

			f.write('Full traces: %d\n' % len(all_traces[k]))
			f.write('-'*80+'\n')
			for t in all_traces[k]:
				for s in t[0]: f.write('%d ' % s)
				f.write('  :  ')
				for s in t[0]: f.write('%s ' % nodes[s]['name'])
				f.write('\n')

				for s in t[1]: f.write('%d ' % s)
				f.write('  :  ')
				for s in t[1]: f.write('%s ' % nodes[s]['name'])
				f.write('\n')

				f.write('-'*60+'\n')
			f.close()


