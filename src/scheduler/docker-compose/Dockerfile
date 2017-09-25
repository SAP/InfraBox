FROM debian

RUN apt-get update -y && apt-get install -y python python-psycopg2 python-requests python-yaml curl
RUN curl -L https://github.com/docker/compose/releases/download/1.16.1/docker-compose-`uname -s`-`uname -m` -o /usr/bin/docker-compose
RUN chmod +x /usr/bin/docker-compose

ADD src/scheduler/docker-compose scheduler

CMD ["python", "scheduler/scheduler.py"]
