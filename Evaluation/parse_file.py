import copy

# Parses the file containing leak and kill bugs and returns
# a list with each element of the form [contract_address, ninvocations, [inputs]]
def parser(filename):
	parse_list = []

	try:
		fp = open(filename, 'r')
	
	except IOError:
		print "The file doesn't exist or couldn't be opened\n"
		exit(0)

	with fp:
		i = 0
		j = i
		temp_list = []
		input_list = []
		for line in fp:
			i+=1
			print line

			linesplit = line.split(":")
			if linesplit[0][:2]=='0x':
				if not len(linesplit[0]) == 42:
					print "This field should have been a contract address\n"
					exit(0)

				temp_list.append(linesplit[0])
				temp_list.append(int(linesplit[1]))
				i=0
				j=i

			else:
				linesplit = line.split(":")
				if not len(temp_list)==2:
					print "Something wrong with the parsing\n"
					exit(0)

				if i-j < int(temp_list[-1]):
					input_list.append(linesplit[0])
				elif i-j == int(temp_list[-1]):
					input_list.append(linesplit[0])
					temp_list.append(input_list)
					parse_list.append(copy.deepcopy(temp_list))
					del temp_list[:]
					del input_list[:]	
				else:
					print "Problem with parsing or parse file"

				


	return parse_list
