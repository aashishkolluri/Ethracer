import opcodes
import os
import sys
import subprocess
import shlex
import argparse
import re
from opcodes import opcodes


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



def disasm(args, key=0):

    temp_list = []
    listindex = []
    complete_disasm = {}
    dictindex = {}
    disasm_out = []

    bin_str=args.replace('\n', '')

    temp_list, listindex, dictindex  = convert(bin_str)
    disasm_out = temp_list
    
    createjumptables(listindex, dictindex, disasm_out)
    # for key1, value in dictindex.iteritems():
        # print key1, '::', value

    if int(key)==1:
        prettyprint(listindex, disasm_out)
        print '\n'

    complete_disasm['test'] = [disasm_out, listindex, dictindex]


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
            print i, hex(listindex[i]).split('x')[1], listindex[i], 'missing opcode'
            
        elif 'PUSH' in item[1]:
            print i, hex(listindex[i]).split('x')[1], listindex[i], item[1],'    ', item[5]

        else:
            print i, hex(listindex[i]).split('x')[1], listindex[i], item[1]    
        i+=1    

def funcfind(start_point, end_point, disasm):
    funclist = []
    for i in range(0, len(disasm)-4):
        if(disasm[i][1]=='PUSH4'):
            hexc = disasm[i][-1]
            if(disasm[i+2][1]=='EQ'):
                if('PUSH' in str(disasm[i+3][1])):
                    if('JUMPI'==disasm[i+4][1]):
                        funclist.append([i, hexc])
            elif(disasm[i+1][1]=='EQ'):
                if('PUSH' in str(disasm[i+2][1])):
                    if('JUMPI'==disasm[i+3][1]):
                        funclist.append([i-1, hexc])
    return funclist 



# print sys.argv[1]
# disasm(sys.argv[1], 1)