FROM python:3.9-slim
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y git curl python3-pip

ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
ENV LANGUAGE en_US:en
ENV TZ=Asia/Kolkata DEBIAN_FRONTEND=noninteractive

WORKDIR /usr/src/app
COPY ./requirements.txt .
RUN chmod 777 /usr/src/app

RUN pip3 install --upgrade pip setuptools wheel
RUN pip3 install -r requirements.txt
RUN apt-get -qq purge git && apt-get -y autoremove && apt-get -y autoclean

COPY . .
RUN chmod 777 /usr/src/app

CMD ["bash", "start.sh"]
