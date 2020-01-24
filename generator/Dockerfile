# sudo docker build -t generator:latest .
# sudo docker run -it generator:latest

FROM mcr.microsoft.com/powershell

RUN apt-get update && apt-get install -y python3 python3-pip \
    && mkdir /home/generator/ /home/generator/res \
    && pip3 install pexpect

COPY scripts /home/generator/scripts
COPY Invoke-Obfuscation /home/generator/Invoke-Obfuscation
COPY generator.py /home/generator/generator.py
COPY obfuscate.ps1 /home/generator/obfuscate.ps1

WORKDIR /home/generator

CMD ["python3","/home/generator/generator.py"]