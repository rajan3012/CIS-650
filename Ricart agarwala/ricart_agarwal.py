i = 1
neighbours = [2,3]

#optimize:
'''
if the process wants the cs for the second time, it doesnt need to ask persmmision to all.
But only ask from process in pending queue. No need to ask all
If pending queue empty, you can access the cs
'''

clock =1

pending = []

priviliged = False

req_stamp = 0 #0 means no request

counter = 0 # number of permissions i have

def get_critical():
    for n in neighbours:
        send_message(n, 'requests', clock,i)
        req_stamp = clock
        counter = 0

def on_permission():
    counter+=1
    if counter == len(neighbours):
        counter = 0
        priviliged = True

def on_request(j,time):
    # if not privileged and if no reqests OR req time less that my req time and if same, j<i (process id)
    # then grant permission
    if (!priviliged and (req_stamp == 0) or ((time,j)<(req_stamp,i))):
        send_message(i,'permission',i)
    else:
        pending.append(j)

def perform_critical():
    #do work here in CS
    priviliged = False
    for p in pending:
        send_message(p,'permission',i)
    req_stamp = 0
    pending = []

while True:
    #do stuff outside of cs
    if cs_needed:
        get_critical()
        while !privileged:
            #do other staff while waiting
        perform_critical()