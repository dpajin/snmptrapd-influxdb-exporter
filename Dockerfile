FROM python:3.11-alpine3.18
LABEL maintainer="Steve Brown https://github.com/audiocomp"

# Install Required Packages
COPY requirements.txt  /tmp/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Add Code & Config
COPY ./mibs /mibs
COPY ./models /models
COPY ./modules /modules
ADD snmptrapd-influxdb-exporter.py .
ADD config.yaml .
ADD README.md .

EXPOSE 162/udp

CMD ["python3","snmptrapd-influxdb-exporter.py"]
