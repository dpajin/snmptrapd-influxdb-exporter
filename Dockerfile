FROM python:3.7.4-alpine3.10

LABEL maintainer="dusan.pajin@gmail.com"

ADD snmptrapd-influxdb-exporter.py /
ADD config.yaml /

RUN pip install influxdb PyYAML
RUN apk --no-cache add net-snmp

# add net-snmp configuration
COPY netsnmp-conf/snmp.conf /etc/snmp/snmp.conf
COPY netsnmp-conf/snmptrapd.conf /etc/snmp/snmptrapd.conf

#add MIBs
COPY mibs/ /usr/share/mibs/

EXPOSE 162

CMD ["snmptrapd","-m","ALL","-f"]