import opcodes
import os
import sys
import subprocess
import shlex
import argparse
import re
from opcodes import opcodes
# from misc import safe_subprocess

# converts the hex value into the opcode string

def convert(bytecode):
	listindex = []
	dictindex = {}
	curr_index = 0
	disasm_out = []



	listindex.append(0)
	while(curr_index < len(bytecode)-2):

		opcode = int('0x' + bytecode[curr_index:curr_index+2], 16)
		
		temp_list = []
		temp_list.append(opcode)

		if opcode in opcodes:
			for item in opcodes[opcode]:
				temp_list.append(item)

			if not 'PUSH' in temp_list[1]:
				listindex.append(listindex[-1]+1) 
			
			if 'PUSH' in temp_list[1]:
				number = int(temp_list[1][4:])
				disasm_out.append(temp_list)
				disasm_out[-1].append(bytecode[curr_index+2:curr_index+2*(number+1)])
				listindex.append(listindex[-1]+1+number)
				curr_index += 2*(number+1)
				continue

			disasm_out.append(temp_list)
			curr_index += 2
			continue

		listindex.append(listindex[-1]+1)
		temp_list.append(-1)
		temp_list.append(opcode)
		disasm_out.append(temp_list)
		curr_index += 2

	return disasm_out, listindex, dictindex    



def disasm(args, key):

	temp_list = []
	listindex = []
	complete_disasm = {}
	dictindex = {}
	disasm_out = []
	solc_cmd = "solc --optimize --bin-runtime %s"

	if '.bin' in args or ('0x' == args[0:2] and not os.path.isfile(args)):
		if not ('0x'==args[0:2] and not os.path.isfile(args)):
			cname = args.split('.bin')[0]+' bytecode'
			fp = open(args, 'r')
			bin_str=fp.read().replace('\n', '')
			print (bin_str)
		else:
			cname = 'bytecode'
			bin_str =  args[2:]

		temp_list, listindex, dictindex   = convert(bin_str)
		disasm_out = temp_list
		
		createjumptables(listindex, dictindex, disasm_out)
		# for key1, value in dictindex.iteritems():
			# print key1, '::', value

		if int(key)==1:
			prettyprint(listindex, disasm_out)
			print ('\n')

		complete_disasm[cname] = [disasm_out, listindex, dictindex]

	else:
		FNULL = open(os.devnull, 'w')
#        solc_p = subprocess.Popen(shlex.split(solc_cmd % args), stdout = subprocess.PIPE, stderr=FNULL)
		solc_p = safe_subprocess( solc_cmd , args, 100, 1 ) 
		solc_out = solc_p.communicate()

		if solc_out[0]=='':
			print ("OOPS! problem with the sol code")
					
		for (cname, bin_str) in re.findall(r"\n======= (.*?) =======\nBinary of the runtime part: \n(.*?)\n", solc_out[0].decode('utf-8')):
			# print "Contract %s:" % cname, "\n"
			# print bin_str
			temp_list, listindex, dictindex   = convert(bin_str)
			disasm_out = temp_list
		
			createjumptables(listindex, dictindex, disasm_out)

			if int(key)==1:
				prettyprint(listindex, disasm_out)
				print ('\n')

			complete_disasm[cname] = [disasm_out, listindex, dictindex]


	return complete_disasm



		

def createjumptables(listindex, dictindex, disasm_out):
	i = 0
	for item in disasm_out:
		dictindex[listindex[i]] = i
		i+=1


def prettyprint(listindex, disasm_out):
	i = 0
	for item in disasm_out:
		if item[1] == -1:
			print (i, hex(listindex[i]).split('x')[1], listindex[i], 'missing opcode')
			
		elif 'PUSH' in item[1]:
			print (i, hex(listindex[i]).split('x')[1], listindex[i], item[1],'    ', item[5])

		else:
			print (i, hex(listindex[i]).split('x')[1], listindex[i], item[1]    )
		i+=1    

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


# print sys.argv[1]
# disasm(sys.argv[1], 1)