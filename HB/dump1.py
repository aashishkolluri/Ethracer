fp = open('file1.txt', 'r')
fp1 = open('file2.txt', 'r')
num = 0
list1 = []
list2 = []

for each in fp.readlines():
	a = each.split('/')[-1]
	b = a.split('-')[0]
	list1.append(b)

for each in fp1.readlines():
	a = each.split('/')[-1]
	b = a.split('-')[0]
	list2.append(b)

for each in list1:
	if each in list2:
		print each
		num+=1

print(num)