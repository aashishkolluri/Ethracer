from web3 import Web3, KeepAliveRPCProvider, IPCProvider


global st
st = {}


# Read storage value
def get_storage_value( address, index, read_from_blockchain = False ):

	if read_from_blockchain:
		web3 = Web3(KeepAliveRPCProvider(host='127.0.0.1', port='8545'))
		value = web3.eth.getStorageAt( address, index )
		return value
	else:
		return 0


# Get some parameters 
def get_params(param, input):

	if (param+input) in st: return st[param+input]
	else:
		print('need to produce')
		print(param+input)
		exit(4)

def set_params(param, input, value):
	global st
	print (param, input, value)
	# if not (param + input) in st:
	st[param+input] = value		


# Create a dict of paramters
def create_params(read_from_blockchain, c_address):

	global st
	st['my_address'] = s.my_address
	st['contract_address'] = c_address
	st['contract_balance'] = s.contract_balance
	
	s.st['gas'] = s.gas
	s.st['gas_limit'] = s.gas_limit
	s.st['gas_price'] = s.gas_price

	s.st['time_stamp'] = s.time_stamp

	s.st['block_number'] = s.block_number


	if read_from_blockchain:
		web3 = Web3(KeepAliveRPCProvider(host='127.0.0.1', port='8545'))
		s.st['contract_balance'] = str(web3.eth.getBalance(c_address)+1).zfill(64)


	if read_from_blockchain:
		global contract_address
		s.contract_address = c_address








