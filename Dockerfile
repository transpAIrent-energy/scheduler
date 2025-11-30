FROM python:3.12-trixie AS base

WORKDIR /srv/ait-scheduler
COPY . /srv/ait-scheduler

WORKDIR /srv/ait-scheduler

RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x ./entrypoint.sh
# remove carriage return before copying to linux
RUN sed -i 's/\r$//' ./entrypoint.sh

CMD ./entrypoint.sh
