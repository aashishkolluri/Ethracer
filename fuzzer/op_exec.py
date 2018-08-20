from __future__ import print_function
import copy
from math import *
from op_list import *
from op_parse import *
from hashlib import *
from sha3 import *
from web3 import Web3, KeepAliveRPCProvider, IPCProvider


global st
st = {}

global undefined
undefined = None

def save_state():
	return copy.deepcopy(st)

def same_state(s1, s2):
	return s1 == s2	

def same_balance(b1,b2):
	for b in b1:
		if b not in b2:
			if b1[b] >0:
				return False
		else:
			if b1[b] != b2[b]: return False

	for b in b2:
		if b not in b1:
			if b2[b] > 0:
				return False
		else:
			if b1[b] != b2[b]: return False
	return True

def pad_address(addr):
	if len(addr) < 42:
		if addr[0:2] == '0x':
			addr = addr[2:]

		addr = addr.rjust(40, '0')
		addr = '0x' + addr

	return addr	

def get_balances():
	balances = {}
	for b in st:
		if b.find('balance') >= 0:
			balances[ b[len('balance'):]] = st[b]
	return balances

def print_balances(bals):
	lb = []
	for b in bals: lb.append( (b,bals[b]))
	slb = sorted(lb,  key=lambda x: x[0] )
	print('Balances:\n---------------------------------------------------------------------------------')
	for b in slb:
		print('%40x : %30x' % (b[0], b[1]))
	print('-------------------------------------------------------------------------------')

def print_balance_difference( b1, b2, f=False ):
		l = []
		# print(b1, b2)
		for b in b1: 
			# print (b)
			if b not in b2: l.append( (b,b1[b], 0))
		for b in b2: 
			if b not in b1: l.append( (b,0, b2[b]))
		for b in b1: 
			if b in b2 and b2[b] != b1[b]: l.append( (b,b1[b],b2[b]))
		sl = sorted(l,  key=lambda x: x[0] )
		if not f:
			print('Balance differences:\n---------------------------------------------------------------------------------')
		else:
			f.write('Balance differences:\n---------------------------------------------------------------------------------'+'\n')
		for b in sl:
			# print(b[0], b[1], b[2])
			if not f:
				print('%40x : %28x   --->  %28x  : %24x' % (int(b[0], 16), b[1], b[2], abs(b[1]-b[2])))
			else:
				f.write('%40x : %28x   --->  %28x  : %24x' % (int(b[0], 16), b[1], b[2], abs(b[1]-b[2]))+ '\n')	

		if not f:		
			print('-------------------------------------------------------------------------------')
		else:
			print('-------------------------------------------------------------------------------\n')	




# Get some parameters 
def get_params(param, input):
	# print('In get params', param, input)
	if param == 'call_data_load' and param in st:
		m = st['call_data_load'][2*input:2*input+64]
		return int( m + '0'*(64-len(m) ) , 16 )
	else:
		# print(st)
		# print(st)
		key = param + str(input)
		# print(key)
		if key in st: return st[key]
		elif param == 'balance':
			return 0
		else:
			print('need to produce')
			print(key)
			return 0

def set_params(param, input, value):
	global st
	# print(param, input, value)
	st[param+str(input)] = value	
	# print(st)	

def clear_params():
	global st
	st = {}

def send_ether(addr_from, addr_to, amount):

	if not isinstance(addr_from, str):
		addr_from = hex(addr_from).rstrip('L').lstrip('0x')

	if not isinstance(addr_to, str):
		addr_to = hex(addr_to).rstrip('L').lstrip('0x')

	addr_from.lstrip('0x').rstrip('L')
	addr_to.lstrip('0x').rstrip('L')		
	# Update contract balance
	from_balance = get_params('balance',addr_from)
	to_balance = get_params('balance',addr_to)
	if from_balance - amount < 0: 
		# print(addr_from, ':', addr_to)
		# print(st)
		print('Not enough Ether to send: %x : %x' % (from_balance, amount))
		return False

	# print('Sent Ether from %s to %s \n'%(addr_from, addr_to))
	# print('initial balance %s:%d , %s:%d \n'%(addr_from, int(from_balance), addr_to, int(to_balance)))	
	from_balance -= amount
	to_balance += amount
	# print('final balance %s:%d , %s:%d \n'%(addr_from, int(from_balance), addr_to, int(to_balance)))
	# print('in send ether ', from_balance, to_balance, amount)
	set_params( 'balance', addr_from, from_balance)
	set_params( 'balance', addr_to, to_balance)
	return True



# Read storage value
def get_storage_value( address, index, st_blocknumber, read_from_blockchain = False ):

	if read_from_blockchain:
		if st_blocknumber < 4350000:
			web3 = Web3(KeepAliveRPCProvider(host='127.0.0.1', port='8666'))
		else:
			web3 = Web3(KeepAliveRPCProvider(host='127.0.0.1', port='8545'))

		value = web3.eth.getStorageAt( address, index )
		return value
	else:
		return 0


def print_stack(stack):
	print('------------------------------------- STACK -------------------------------------')
	for s in stack[::-1]:
		if s == undefined: 
			print('undefined')
		else:
			if isinstance(s, str):
				print(s)
			else:	
				print('%64x' % s)

def print_storage(storage):
	print('************************************ STORAGE ************************************')
	for fl in storage:
		print('\033[91m[ %64x ] \033[0m : ' % (fl), end='' )        
		if fl == undefined: print('undefined')
		else:print('%64x' % storage[fl])



def unary( o1, step, op='NONE' ):

	if o1 == undefined: return undefined

	if      op == 'NOT': return (~o1) % (2**256)
	elif    op == 'ISZERO': return 1 if (o1 == 0) else 0
	else:
		print('did not process unary operation %s ' % op )
		print(o1)
		return undefined 

def binary( o1, o2 , step, op='NONE'):


	# In some cases the result can be determined with the knowledge of only one operand
	if not (o1 == undefined) :
		if op in ['MUL','AND','DIV','SDIV'] and 0 == o1: return 0 
		if op in ['XOR','ADD'] and 0 == o1: return o2
		
	if not (o2 == undefined ) :
		if op in ['MUL','AND','DIV','SDIV'] and 0 == o1: return 0
		if op in ['XOR','ADD'] and 0 == o2: return o1

	if o1 == undefined or o2 == undefined: return undefined 

#    print('%s : %x %x' % (op, o1, o2) )

	if   op =='AND' : return o1 & o2
	elif op =='OR'  : return o1 | o2
	elif op =='XOR' : return o1 ^ o2
	elif op =='ADD' : return (o1 + o2) % (2**256)
	elif op =='SUB' : return o1 - o2 
	elif op =='EXP' : return (o1 ** o2) % (2**256)
	elif op =='DIV' : return 0 if 0==o2 else o1 // o2 
	elif op =='MOD' : return 0 if 0==o2 else o1 % o2 
	elif op =='MUL' : return (o1 * o2) % (2**256) 
	elif op =='GT'  : 
		o1 = o1 if o1 >= 0 else o1 + 2**256
		o2 = o2 if o2 >= 0 else o2 + 2**256
		return (o1>o2) 
	elif op =='SGT' : return (o1>o2)
	elif op =='LT'  : 
		o1 = o1 if o1 >= 0 else o1 + 2**256
		o2 = o2 if o2 >= 0 else o2 + 2**256
		return (o1<o2)
	elif op =='SLT' : return (o1<o2)
	elif op =='EQ'  : return (o1==o2)
	else:
		print('did not process binary operation %s  ' % op)
		print(o1)
		print(o2)
		return undefined



def ternary( o1, o2 , o3, step, op='NONE'):

	if 0 == o3: return 0

	if o1 == undefined or o2 == undefined or o3 == undefined: return undefined

	if   op == 'ADDMOD': return (o1+o2) % o3 
	elif op == 'MULMOD': return (o1*o2) % o3 
	else:
		print('did not process ternary operation %s  ' % op)
		print(o1)
		print(o2)
		print(o3)
		return undefined  


def execute( code, stack, pos, storage, temp_storage, mmemory, data, st_blocknumber, debug=False, read_from_blockchain = False ):
	if debug: print(code[pos]['o'])
	if debug: print_stack(stack)
	op = code[pos]['o']
	ret = False
	step = code[pos]['id']

	# print(op)
	# print_stack(stack)


	if op not in allops:
		print('Does not understand the operation %s at pos %x' % (op,pos) )
		return stack,pos,True, mmemory

	if allops[op][1] > len(stack): 
		if debug: print('Not enough entries in the stack to execute the operation %8s  : %x' % (op,code[pos]['id']) )
		return stack, pos, True, mmemory

	if op in ['ISZERO','NOT']:
		stack.append( unary ( stack.pop(),step, op ) )

	if op in ['ADD','MUL','SUB','DIV','SDIV','MOD','SMOD','EXP','SIGNEXTEND','AND','OR','XOR', 'LT','GT','SLT','SGT','EQ']:
		stack.append( binary (  stack.pop() , stack.pop() , step , op ) )

#		print('%x' % stack[-1])


	if op in ['ADDMOD','MULMOD']: 
		stack.append( ternary( stack.pop(), stack.pop(), stack.pop(), step, op ) )

	if op == 'BYTE':
		print('Incorrectly implemented BYTE')
		byte_no = stack.pop()
		word   = stack.pop()
		stack.append(undefined)

	if op == 'SHA3':

		exact_address  = stack.pop()
		exact_offset= stack.pop()

		res = undefined 

		if not (exact_address == undefined)  and not (exact_offset == undefined) and exact_offset >= 0:
			if (exact_offset % 32) == 0 :     # for now, can deal only with offsets divisible by 32

				val = ''
				all_good = True
				for i in range(exact_offset//32):
					if (exact_address + i*32) not in mmemory or mmemory[exact_address+i*32] == undefined: 
						all_good = False
						break
					val += '%064x' % mmemory[exact_address + i*32]


				if all_good:

					k = keccak_256()
					k.update(val.decode('hex'))
					digest = k.hexdigest()
					res = int(digest,16) 

		stack.append( res )


	if op in ['BLOCKHASH']:
		o1 = stack.pop()
		k = keccak_256()
		k.update( ('%x' % o1).encode('utf-8') ) 	# not quite correct implementation of BLOCKHASH
		digest = k.hexdigest()
		stack.append( int(digest,16) )

	if op in ['NUMBER']: stack.append( get_params('blocknumber','') )

	if op in ['GASLIMIT']: stack.append( 0 )

	if op == 'INVALID': ret = True

	if op == 'TIMESTAMP': stack.append( get_params('timestamp','') )

	if op == 'COINBASE':  stack.append( get_params('coinbase','') ) 

	if op == 'DIFFICULTY': stack.append( get_params('difficulty','') )

	if op in ['POP']: stack.pop()

	if op.find('PUSH') >= 0:  stack.append( int(code[pos]['input'],16) )

	if op.find('DUP') >= 0: stack.append( copy.deepcopy( stack[-int(op[3:]) ] ) )

	if op.find('SWAP') >= 0:
		tmp1 = stack[-1]
		tmp2 = stack[-int(op[4:])-1 ]
		stack[-1] = tmp2
		stack[-int(op[4:]) -1] = tmp1

	if op.find('LOG') >= 0:
		for j in range( int(op[3:]) ):
			stack.pop()
		stack.pop()
		stack.pop()

	if op in ['CALLVALUE']: stack.append( get_params('call_value','') )

	if op in ['JUMPDEST']: pass

	if op in ['CODECOPY']:
		print('Incorrectly implemented COINBASE/DIFFICULTY')
		stack.pop()
		stack.pop()
		stack.pop()

	if op in ['STOP','REVERT']: ret = True

	if op == 'ADDRESS': stack.append( int(get_params('contract_address',''), 16 ))

	if op == 'ORIGIN' : stack.append( get_params('origin','') )

	if op == 'BALANCE':
		addr = stack.pop()
		if addr == undefined: 
			print('BALANCE address is undefined')
			return stack, pos, True, mmemory

		if not isinstance(addr, str):
			addr = hex(addr).lstrip('0x').rstrip('L')

		addr = addr.lstrip('0x').rstrip('L')	
		# print (addr)
		stack.append( get_params('balance',addr) )

	if op == 'CALLER': stack.append( get_params('caller','') )

	if op in ['CALLDATALOAD']:
		addr = stack.pop()
		if addr == undefined:
			print ('\033[95m[-] In CALLDATALOAD the input address cannot be determined at step %x: \033[0m' % code[pos]['id'] )
			return stack, pos, True, mmemory

		stack.append( get_params('call_data_load', addr) )

	if op in ['CALLDATASIZE']: stack.append( get_params('call_data_size','') )

	if op in ['CALLDATACOPY']:
		print('Incorrectly implemented CALLDATACOPY')
		addr   = stack.pop()
		idata  = stack.pop()
		offset = stack.pop()


	if op == 'GASPRICE': stack.append( get_params('gas_price','') )

	if op == 'CREATE':
		print('Incorrectly implemented CREATE')
		stack.pop()
		stack.pop()
		stack.pop()
		stack.append( 0 )

	if op == 'CALL':

		args = []
		for i in range(7): args.append( stack.pop())
		if args[1] != undefined and args[2] != undefined and args[4] == 0 and args[6] == 0:

			sent_amount_ether = args[2]
			contract_address = get_params('contract_address','')
			receive_address = args[1]
			contract_address = contract_address.lstrip('0x')
			receive_address = hex(receive_address).lstrip('0x').rstrip('L')
			snt = send_ether ( contract_address, receive_address, sent_amount_ether)
			stack.append( 1 if snt else 0 )

		else:			
			print('Incorrectly implemented CALL')
			print_stack(stack[-7:])
			print_storage(storage)
			stack.append( 0 )

	if op == 'CALLCODE':
		print('Incorrectly implemented CALLCODE')
		stack.pop()
		stack.pop()
		stack.pop()
		stack.pop()
		stack.pop()
		stack.pop()
		stack.pop()
		stack.append( undefined )

	if op in ['RETURN']:
		print('Incorrectly implemented RETURN')
		stack.pop()
		stack.pop()
		ret = True

	if op == 'DELEGATECALL':
		print('Incorrectly implemented DELEGATECALL')
		stack.pop()
		stack.pop()
		stack.pop()
		stack.pop()
		stack.pop()
		stack.pop()
		stack.append( undefined )

	if op in ['SUICIDE']:
		stack.pop()
		ret = True

	if op == 'EXTCODESIZE':
		print('Incorrectly implemented RETURN')
		stack.pop()
		stack.append( 0 )


	if op == 'MLOAD':
		addr = stack.pop()

		if addr == undefined:
			if debug:print('\033[95m[-] The MLOAD address on %x  cannot be determined\033[0m' % code[pos]['id'] )
			return stack, pos, True, mmemory


		if addr in mmemory: res = copy.deepcopy(mmemory[addr])
		else: res = 0

		stack.append( res )


	if op == 'MSTORE':

		addr = stack.pop()
		if addr == undefined:
			stack.pop()
			if debug:print('\033[95m[-] The MSTORE the write address on %x  cannot be determined\033[0m' % code[pos]['id'] )
			return stack, pos, True, mmemory

		mmemory[addr] = stack.pop();


	if op in ['MSTORE8']:
		print('Incorrectly implemented RETURN')
		addr = stack.pop()
		value= stack.pop()


	if op == 'SLOAD':
		addr = stack.pop()
		if addr == undefined:
			print('nod')
			if debug:print('\033[95m[-] The SLOAD address on %x  cannot be determined\033[0m' % code[pos]['id'] )
			return stack, pos, True, mmemory

		if addr in storage: 
			res = copy.deepcopy(storage[addr])
		elif addr in temp_storage:	
			res = copy.deepcopy(temp_storage[addr])
		else:
			
			if read_from_blockchain:
				if st_blocknumber < 4350000:
					web3 = Web3(KeepAliveRPCProvider(host='127.0.0.1', port='8666'))

				if st_blocknumber >= 4350000:
					web3 = Web3(KeepAliveRPCProvider(host='127.0.0.1', port='8545'))

				contract_address = get_params('contract_address','')
				contract_address_new = contract_address
				if not isinstance(contract_address_new, str):
					contract_address_new = str(contract_address_new).rstrip('L')

				if contract_address_new[-1]=='L': contract_address_new = contract_address_new.rstrip('L')
				# print(contract_address_new)	
				contract_address_new = pad_address(contract_address_new)
				value = web3.eth.getStorageAt( contract_address_new , addr , st_blocknumber)
				if value[0:2] == '0x': value = value[2:]
				value = int(value,16)
			else:
				value = 0

			temp_storage[addr] = value	
			# storage[addr] = value
			# print(temp_storage)
			res = copy.deepcopy(value)


		stack.append( res )



	if op == 'SSTORE':

	    addr = stack.pop()
	    if addr== undefined:
	        stack.pop()
	        if debug:print('\033[95m[-] The SSTORE address on %x  cannot be determined\033[0m' % code[pos]['id'] )
	        return stack, pos, True, mmemory

	    storage[addr] = stack.pop();
	    # temp_storage[addr] = copy.deepcopy(storage[addr])

			
	if op == 'JUMP':


		if len(stack) < 1:
			if debug: print('\033[95m[-] In JUMP the |stack|=%2d is too small to execute JUMP\033[0m' % len(stack) )
			return stack, pos, True, mmemory
		
		addr = stack.pop()


		if addr == undefined :
			if debug: print('\033[95m[-] In JUMP the address cannot be determined \033[0m'  )
			return stack, pos, True, mmemory

		jump_dest = addr 
		if( jump_dest <= 0):
			if debug: print('\033[95m[-] The JUMP destination is not a valid address : %x\033[0m'  % jump_dest )
			return stack, pos, True, mmemory

		new_position= find_pos(code, jump_dest )
		if( new_position < 0):
			if debug: print('\033[95m[-] The code has no such JUMP destination: %s at line %x\033[0m' % (hex(jump_dest), code[pos]['id']) )
			return stack, pos, True, mmemory


		return stack, new_position, ret, mmemory


	if op == 'JUMPI':
		addr = stack.pop()
		des = stack.pop()

		if des == undefined or des == undefined :
			if debug: print('\033[95m[-] In JUMPI the expression cannot be evaluated (is undefined)\033[0m'   )
			return stack, pos, True, mmemory

		if des != 0: 
			new_position = find_pos(code, addr )
			if( new_position < 0):
				if debug: print('\033[95m[-] The code has no such jump destination: %s at line %x\033[0m' % (hex(addr), code[pos]['id']) )
				return stack, pos, True, mmemory
			else:
				return stack, new_position, ret, mmemory


	if op == 'MSIZE':   #have to correct later
		print('Incorrectly implemented MSIZE')
		stack.append( len(mmemory) )

	if op == 'GAS':   stack.append( get_params('gas','') )

	return stack, pos + 1, ret, mmemory


