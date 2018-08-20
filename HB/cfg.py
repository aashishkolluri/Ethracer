
from __future__ import print_function
import networkx as nx
from z3 import *

def build_cfg(ops, opers, debug, read_from_blockchain):


	jumpdest = {}
	for i in range(len(ops)):
		if ops[i]['o'] == 'JUMPDEST':
			jumpdest[ops[i]['id']] = i


	nodes = {}
	edges = []
	current_start = 0
	d_oper = {}
	for o in opers: d_oper[o] = False

	for i in range(len(ops)):

		o = ops[i]
		if o['o'] in opers: d_oper[o['o']] = True


		if o['o'] == 'JUMPI' and i > 0 and i+1 < len(ops):

			# Finish current node
			nodes[current_start] = {'end':ops[i-1]['id']}
			for o in d_oper: nodes[current_start][o] = d_oper[o]

			# Add edges for

			# the node that start at the next line
			edges.append( (current_start, ops[i+1]['id'] ) )


			# the node that starts at the jump
			if ops[i-1]['o'].find('PUSH') >= 0:
				jump = int(ops[i-1]['input'],16)
				if jump in jumpdest:
					edges.append( (current_start, jump ) )
			else:
				pass
			

			for o in opers: d_oper[o] = False
			if i+1 < len(ops):
				current_start = ops[i + 1]['id']
			



		elif o['o'] == 'JUMP' and i > 0 :
		
			# Finish current node
			nodes[current_start] = {'end':ops[i-1]['id']}
			for o in d_oper: nodes[current_start][o] = d_oper[o]

			# Add edges for:
			# the node that starts at the jump
			if ops[i-1]['o'].find('PUSH') >= 0:
				jump = int(ops[i-1]['input'],16)
				if jump in jumpdest:
					edges.append( (current_start, jump ) )
			else:
				pass
		

			for o in opers: d_oper[o] = False
			if i+1 < len(ops):
				current_start = ops[i + 1]['id']


		elif o['o'] == 'JUMPDEST' and i > 0:
		
			# Finish current node
			nodes[current_start] = {'end':ops[i-1]['id']}
			for o in d_oper: nodes[current_start][o] = d_oper[o]

			# Add edges for:
			# the node that start at the next line
			edges.append( (current_start, ops[i]['id'] ) )

			current_start = ops[i]['id']

		elif o['o'] in ['RETURN','STOP','REVERT','INVALID','SUICIDE'] and i > 0 :

			# Finish current node
			nodes[current_start] = {'end':ops[i]['id']}
			for o in d_oper: nodes[current_start][o] = d_oper[o]

			for o in opers: d_oper[o] = False
			if i+1 < len(ops):
				current_start = ops[i+1]['id']



	# Finish the last node
	nodes[current_start] = {'end':ops[i-1]['id']}
	for o in d_oper: nodes[current_start][o] = d_oper[o]


	return nodes, edges

def get_valid_nodes(nodes,edges, type_of_special_nodes):


	G = nx.DiGraph()
	seen_nodes = []
	for e in edges:
		G.add_edge( e[0],e[1])
		if e[0] not in seen_nodes: seen_nodes.append(e[0])
		if e[1] not in seen_nodes: seen_nodes.append(e[1])


	special_nodes = []
	for n in nodes:
		for t in type_of_special_nodes:
			if t in nodes[n] and nodes[n][t] and n not in special_nodes : special_nodes.append(n)



	good_nodes = []
	for special_node in special_nodes:	
		if special_node in seen_nodes:
			for en in seen_nodes:
				if   en not in good_nodes and nx.has_path(G,en,special_node): good_nodes.append(en)
				elif en not in good_nodes and nx.has_path(G,special_node,en): good_nodes.append(en)


	return good_nodes


	

def get_nodes(nodes,type_of_special_nodes):

	good_nodes = []
	for n in nodes:
		for t in type_of_special_nodes:
			if t in nodes[n] and nodes[n][t] and n not in good_nodes:
				good_nodes.append(n)


	return good_nodes

def get_all_nodes(nodes):

	good_nodes = []
	for n in nodes:
		good_nodes.append(n)
	return good_nodes



def get_good_jumps(ops, special_ins, debug, read_from_blockchain ):


	# Build CFG
	nodes,edges = build_cfg( ops, ['SSTORE'] + special_ins, debug, read_from_blockchain )

	# Find all nodes that are reachable from/to some SSTORE
	# These are important nodes because they may change global variables and thus make some paths to SUICIDE feasible
	sstore_nodes = get_valid_nodes( nodes, edges, ['SSTORE'])

	# Find all nodes that are reachable from/to some SUICIDE
	suicid_nodes = get_valid_nodes( nodes, edges, special_ins )

	# Further consider only those nodes (i.e. SSTORE + special ins)
	# That is, consider only jumps to code instructions that either change global variables or lead to special instructions
	temp_good_jump_positions = []
	for sn in sstore_nodes:
		if sn not in temp_good_jump_positions: temp_good_jump_positions.append(sn)
	for sn in suicid_nodes:
		if sn not in temp_good_jump_positions: temp_good_jump_positions.append(sn)


	return temp_good_jump_positions

