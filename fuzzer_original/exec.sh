
for((i=0; i<$1; i++)) 
do 
    nohup python main.py --par $i $1  > out$i.txt & 
done
