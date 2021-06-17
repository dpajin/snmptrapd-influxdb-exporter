FROM python:3.9-alpine3.13

LABEL maintainer="Steve Brown https://github.com/audiocomp"

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

ip_input_state{CARD="1", CONFIG_ID="021496f2-6636-4c44-9d1a-89132ce9ccbf", HOST="10.144.120.52", LABEL="SD", MCAST="239.16.0.1:20000", instance="192.168.12.82:8000", job="prometheus-ipgateway-uuids"}
ip_output_state{CARD="1", CONFIG_ID="899edd8e-2793-48e6-bb89-1c870a2c4e86", HOST="10.144.120.50", LABEL="1080p50", MCAST="239.16.0.4:20000", instance="192.168.12.82:8000", job="prometheus-ipgateway-uuids"}

10.144.120.50:443, Slot 1, 899edd8e-2793-48e6-bb89-1c870a2c4e86,
instance CARD CONFIG_ID

sum(node_disk_bytes_read * on(instance) group_left(node_name) node_meta{}) by (node_name)

 * on(CONFIG_ID) group_left(LABEL, MCAST) ip_input_state
  * on(CONFIG_ID) group_left(LABEL, MCAST) ip_output_state