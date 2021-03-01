FROM python:3.9-alpine3.13

LABEL maintainer="steve@audiocomp.co.uk"

ADD snmptrapd-influxdb-exporter.py /
ADD config.yaml /

RUN pip install influxdb-client PyYAML
RUN apk --no-cache add net-snmp

# add net-snmp configuration
COPY netsnmp-conf/snmp.conf /etc/snmp/snmp.conf
COPY netsnmp-conf/snmptrapd.conf /etc/snmp/snmptrapd.conf

#add MIBs
COPY mibs/ /usr/share/mibs/

EXPOSE 162

CMD ["snmptrapd","-m","ALL","-f"]