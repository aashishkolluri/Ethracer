import pprint
import subprocess
import re
import os
import argparse


def get_active_outputs(max_num):
    actives = []
    devnull = open(os.devnull, 'w')
    for i in range(max_num):
        ps = subprocess.Popen(['fuser', 'out'+str(i)+'.txt'], stdout=subprocess.PIPE, stderr=devnull)
        out,err = ps.communicate()
        if len(out) > 2: # and int(out) > 10:
            actives.append(i)
    return actives


no_cores = 30

parser = argparse.ArgumentParser()
parser.add_argument("--cores",        type=str,   help="Compile contract", action='store')

args = parser.parse_args()

if args.cores:
    no_cores = int(args.cores)


print('NO cores: %d' % no_cores)


active_outputs = get_active_outputs(32)
print('active_outputs: ', active_outputs)



# start instances that are not foudn in active_outptus

with open('toexec.sh','w') as f:
    f.write('echo "Start running"\n')
    for i in range(no_cores):
        if i not in active_outputs:
            print('will start %d' % i)
            f.write('nohup python main.py --par  '+ str(i)+' ' + str(no_cores)+' oyente_flagged1.txt >> out'+str(i)+'.txt &\n')
            f.write('sleep .5\n')

    f.close()


