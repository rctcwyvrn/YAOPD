# sudo docker build -t generator:latest .
# sudo docker run -v <path to repo>/powershell/generator/res/:/home/generator/res/ -it generator:latest <number of files to generate> <thread #>
# On josh's machine:
# sudo docker run -v /home/bingley/Projects/YAOPD/generator/res:/home/generator/res/ -it generator:latest <number of files to generate> <thread #>

FROM mcr.microsoft.com/powershell

RUN apt-get update && apt-get install -y python3 python3-pip time\
    && mkdir /home/generator/ /home/generator/res \
    && pip3 install pexpect

COPY scripts /home/generator/scripts
COPY Invoke-Obfuscation /home/generator/Invoke-Obfuscation
COPY generator.py /home/generator/generator.py
COPY obfuscate.ps1 /home/generator/obfuscate.ps1

WORKDIR /home/generator

# ENTRYPOINT ["/usr/bin/time","/usr/bin/python3","/home/generator/generator.py"]
ENTRYPOINT ["/usr/bin/python3","/home/generator/generator.py"]