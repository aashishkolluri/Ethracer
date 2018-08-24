from web3 import Web3, KeepAliveRPCProvider, IPCProvider
import copy
from z3 import *
import datetime

def optimize_hb(hb_list):
	simplified_hb = []

	for item in hb_list:
		if item not in simplified_hb:
			temp = ()
			temp += (item[1], )
			temp += (item[0], )

			if not temp in hb_list:
				simplified_hb.append(copy.deepcopy(item))
	return simplified_hb			

# Read storage value
def get_storage_value( address, index, read_from_blockchain = False ):

	if read_from_blockchain:
		if MyGlobals.STORAGE_AT_BLOCK < 4350000:
			web3 = Web3(KeepAliveRPCProvider(host='127.0.0.1', port='8666'))
		else:
			web3 = Web3(KeepAliveRPCProvider(host='127.0.0.1', port='8545'))

		if MyGlobals.STORAGE_AT_BLOCK >= 0:
			value = web3.eth.getStorageAt( address, index, MyGlobals.STORAGE_AT_BLOCK )
		else:
			value = web3.eth.getStorageAt( address, index )
		return value
	else:
		return '0'.zfill(64)

# Get value 
def get_params(param, input):

	if (param+str(input)) in MyGlobals.st:
		return MyGlobals.st[param+str(input)]
	else:
		print('need to set the parameters: %s ' % (param+str(input) ) )
		exit(4)

# Is set
def is_params(param,input):
	return (param+str(input)) in MyGlobals.st 

# Set parameter
def set_params(param, input, value):
	global st
	MyGlobals.st[param+str(input)] = value		

# Create a dict of paramters
def initialize_params(read_from_blockchain, c_address, nsolutions):

	# Set (dummy) values for parameters often used in the contracts
	global st
	MyGlobals.max_solutions = nsolutions
	MyGlobals.st = {}
	MyGlobals.st['my_address'] = ('6' * 40).zfill(64)
	MyGlobals.st['contract_address'] = c_address
	MyGlobals.st['contract_balance'] = '7' * 64
	MyGlobals.st['gas'] = ('765432').zfill(64)
	MyGlobals.st['gas_limit'] = ('%x' % 5000000).zfill(64)
	MyGlobals.st['gas_price'] = ('123').zfill(64)
	MyGlobals.st['time_stamp'] = ('%x' % 0x7687878).zfill(64)
	MyGlobals.st['block_number'] = ('545454').zfill(64)
	MyGlobals.st['caller'] = [('11' * 20).zfill(40), ('22' * 20).zfill(40)]

def print_params():
	for s in MyGlobals.st:
		print('%20s : %s' % (s, str(MyGlobals.st[s])))

def update_global_datastructures(stack, storage, sha3_dict, sha3_values, data) :
	MyGlobals.datastructures['stack'] = copy.deepcopy(stack)
	MyGlobals.datastructures['storage'] = copy.deepcopy(storage)
	MyGlobals.datastructures['sha3_dict'] = copy.deepcopy(sha3_dict)
	MyGlobals.datastructures['data'] = copy.deepcopy(data)
	MyGlobals.datastructures['sha3_values'] = copy.deepcopy(sha3_values)

def create_configuration( stack, mmemory, storage):
	nc = {}
	nc['stack']   = copy.deepcopy(stack)
	nc['mmemory'] = copy.deepcopy(mmemory)
	nc['storage'] = copy.deepcopy(storage)
	return nc
	
def add_configuration( step, configurations, nc):
	if step in configurations: configurations[step].append( nc )
	else:configurations[step] = [nc]
	

def configuration_exist(step, configurations, nc):
	if step not in configurations:
		return False
	
	found = False
	for os in configurations[step]:

		# Compare stack
		if os['stack'] != nc['stack'] : continue
		
		# Compare mmemory
		if os['mmemory'] != nc['mmemory']: continue

		# Compare storage
		if( os['storage'] != nc['storage'] ):continue
			
		found = True
		break
		
	return found 
	
def seen_configuration( configurations, ops, position, stack, mmemory, storage):

		# Check if configuration exist
		op = ops[position]['o']
		step = ops[position]['id']
		nc = create_configuration( stack, mmemory, storage)
		if configuration_exist(step, configurations, nc): 
			return True
		else:
			add_configuration( step, configurations, nc)
				
		return False
		
def print_configuration( conf ):
	for c in conf:
		print_stack(  c['stack'] )
		print_storage(c['storage'])


class MyGlobals(object):

	# STORAGE_AT_BLOCK = -1
	STORAGE_AT_BLOCK = 4350000

	set_storage_symbolic = False
	jumpi_switch = False

	MAX_JUMP_DEPTH 			= 50					# path length in CFG
	MAX_CALL_DEPTH 			= 1						# different function calls to the contract
	# MAX_VISITED_NODES      	= 2000					# sum of all paths in search of one contract
	MAX_VISITED_NODES      	= 20000					# sum of all paths in search of one contract

	MIN_CODE_SIZE = 4
	MAX_CODE_SIZE = 15000


	ETHER_LOCK_GOOD_IF_CAN_CALL = True

	st = {}

	#
	# Z3 solver
	# 
	SOLVER_TIMEOUT = 10000			#timeout
	s = Solver()
	s1 = Solver()
	s2 = Solver()
	s.set("timeout", SOLVER_TIMEOUT)
	solver_configurations = {}

	search_condition_found = False
	solution_found = False
	in_sha3 = 0
	stop_search = False
	visited_nodes = 0

	fast_search = True	
	good_jump_positions = []

	last_eq_step = -1
	last_eq_func = -1
	num_functions = -1
	functions = []

	symbolic_vars = []
	no_function_calls = 0
	function_calls = {}

	max_solutions = 3
	max_jumpdepth_in_normal_search = 600

	datastructures = {}
	# The datastructure which stores all global variables that a function could change
	funcvardata = {}
	sha3vardata = {}
	solution_dict = {}
	# Determines the max time allowed to check one contract
	# Set timeout to < 1 in order to ignore it
	ONE_CONTRACT_HB_TIMEOUT = 120 * 60
	Time_checkpoint_HB = datetime.datetime.now()
	ONE_HB_TIMEOUT = 2 * 60
	Time_checkpoint = datetime.datetime.now()

	num_solver_calls = 0
	total_time_solver = 0
	# Determines number of nodes traversed through

	notimplemented_ins = {}

def clear_globals():

	MyGlobals.s.reset() 
	MyGlobals.s1.reset()
	MyGlobals.s2.reset()
	MyGlobals.s.set("timeout", MyGlobals.SOLVER_TIMEOUT)
	MyGlobals.s1.set("timeout", MyGlobals.SOLVER_TIMEOUT)
	MyGlobals.s2.set("timeout", MyGlobals.SOLVER_TIMEOUT)

	MyGlobals.search_condition_found = False
	MyGlobals.stop_search = False
	MyGlobals.visited_nodes = 0
	MyGlobals.no_function_calls = 0
	MyGlobals.function_calls = {}



	

