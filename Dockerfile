
FROM python:3.11
WORKDIR /Discordwebheadbot
COPY requirements.txt  /Discordwebheadbot/
RUN pip install -r requirements.txt
COPY . /Discordwebheadbot
CMD python main.py
RUN apt-get update
RUN apt-get install ca-certificates