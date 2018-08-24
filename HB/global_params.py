''' Uncomment the below line to do analysis at ay specific block. If you specify the --atbock argument in the terminal, this is not required.'''

# STORAGE_AT_BLOCK = 4350000

''' Change to stop reading storage from blockchain. If you specify the --blockchain argument in the terminal, this is not required.'''

READ_FROM_BLOCKCHAIN = True

''' Change to 0 to check for balance defferences in the dynamic analysis '''

CHECK_FOR_BALANCE = 1

''' Uncomment for changing maximum JUMPS until which the analysis has to be performed. Hint: more jumps => more analysis, also more time. '''

# MAX_JUMP_DEPTH = 50				


''' Uncomment the below line for changing the maximum number of visited nodes during static analysis. '''

# MAX_VISITED_NODES = 20000				


''' Change the maximum number of nodes output by the static analysis engine, per wHB relation. \
If you specify the --nsolutios argument in the terminal, this is not required.'''

MAX_SOLUTIONS = 3



'''
	Timeouts
'''

''' Uncomment the below line to change the solver timeout in seconds. '''

# SOLVER_TIMEOUT = 10000	


''' Uncomment to change the max time allowed to check one contract. '''

# ONE_CONTRACT_HB_TIMEOUT = 120 * 60


''' Uncomment to change the max time for analysis of one wHB relation. '''

# ONE_HB_TIMEOUT = 2 * 60