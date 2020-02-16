# sudo docker build -t generator:latest .
# sudo docker run -v <path to repo>/powershell/generator/data/:/home/generator/data/ -it generator:latest <number of files to generate> <thread #>

FROM mcr.microsoft.com/powershell

RUN apt-get update && apt-get install -y python3 python3-pip\
    && mkdir /home/generator/ /home/generator/data /home/generator/data/res \
    && pip3 install pexpect

COPY scripts /home/generator/scripts
COPY Invoke-Obfuscation /home/generator/Invoke-Obfuscation
COPY generator.py /home/generator/generator.py

WORKDIR /home/generator

ENTRYPOINT ["/usr/bin/python3","/home/generator/generator.py"]