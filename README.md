# snmptrapd-influxdb-exporter

This is a SNMP Trap collector based on *net-snmp* package *snmptrapd*, which then provides an export to InfluxDB v2.x using a custom Python script. 
The project is forked from https://github.com/dpajin/snmptrapd-influxdb-exporter.git which provides support for InfluxDB v1.x

## How to use it and how it works

### 1. Clone the repo
```
git clone https://github.com/audiocomp/snmptrapd-influxdb-exporter.git
cd snmptrapd-influxdb-exporter
```

### 2. Add the required SNMP MIBs
Any SNMP MIB files that should be used for SNMP Traps processing should be placed in the directory `mibs/`. The content of this directory will be copied to the docker container in the `/usr/share/mibs/`, according to the statement in the `Dockerfile`.

To add *Juniper* SNMP MIBs in the `mibs` directory, use the following:
```
wget https://www.juniper.net/documentation/software/junos/junos192/juniper-mibs-19.2R1.8.tgz
tar -xvf juniper-mibs-19.2R1.8.tgz -C mibs
rm -f juniper-mibs-19.2R1.8.tgz
ls -al mibs/
```

In the configuration file located at `net-snmp/snmp.conf` is the *net-snmp* configuration. This file needs to list all directories containing SNMP MIB files that are to be loaded. By default /usr/share/mibs/ is included.

Additional subdirectories may be added to `net-snmp/snmp.conf`:
```
mibdirs +/usr/share/mibs/JuniperMibs
mibdirs +/usr/share/mibs/StandardMibs
```

### 3. Configure snmptrapd
The *snmptrapd* has an option to execute custom script upon receipt of a SNMP Trap. It will provide data from the parsed SNMP Trap as standard input into the custom python script. 
This is controlled by configuration file located in `net-snmp/snmptrapd.conf`. The following two lines are important from this configuration file:
```
authCommunity execute public
traphandle default python /snmptrapd-influxdb-exporter.py
```
The first line defines what will be the action for the community used. The default accepted community is `public`. Additional communities may be added to `net-snmp/snmptrapd.conf`:
```
authCommunity execute community
```

If the system is to be used to process SNMPv3 Traps or Informs, that should be configured in this file as well. There are some Commented Samples in the config file. Please consult *net-snmp* and *snmptrapd* documentation on how to configure SNMPv3 traps and Informs. 

The second line defines how  received SNMP Traps will be handled. This line specifies that the Python script   `snmptrapd-influxdb-exporter.py`, located in the `/` directory will be executed for each SNMP Trap.

### 4. Configure the Processing Script
The processing of SNMP Traps is done by: `snmptrapd-influxdb-exporter.py`. 
The script's processing functions can be configured using `config.yaml` file.

The configuration file has the following sections:

`Tune logging level:`
```
logging: ERROR
```

Change to DEBUG to aid Error Handling

`Configure destination InfluxDB servers:`
Change the InfluxDB server IP address and tune the database access parameters. The configured bucket should already exist on the InfluxDB server. There can be more than one server configured.
```
influxdb:
  server:
    - name: local
      url: http://172.17.0.2:8086
      org: snmptraps
      token: influx-snmptraps
      bucket: snmptraps
```


`Configure the Default Trap Processing Options:'
The *all* section defines how all of the traps will be processed. All traps will be exported to the same influxDB *measurement*, as configured in this section.
```
all:
  measurement: snmptraps
  tags:
    host_dns: host_name
    host_ip: host_ip
    oid: oid
```

InfluxDB *measurement* *tags* can be customized here, for the  *measurement* *field* called *varbinds*. It consist of a comma-sepratated list of varbinds in the following format: `oid1=value1, oid2=value2, ...`

It is possible to add permit and deny lists here, to filter traps based on snmpTrapOID value. 
The *permit* list takes precedence, so if it is configured, only Traps matched with entries in the list will be accepted and all other will be denied. 
If the *permit* list is not configured, but the *deny* list exists, it will accept all Traps except those configured in the *deny* list.
If neither of the lists are configured, all SNMP Traps will be accepted.

Example *Permit* configuration:
```
all:
  measurement: snmptraps
  tags:
    host_dns: host_name
    host_ip: host_ip
    oid: oid
  permit:
    - IF-MIB::linkUp
    - linkDown
```

Example *Deny* configuration:
```
all:
  measurement: snmptraps
  tags:
    host_dns: host_name
    host_ip: host_ip
    oid: oid
  deny:
    - JUNIPER-CFGMGMT-MIB::jnxCmCfgChange
```

`Example Default output from the database:`
```
time                host_name host_ip  oid                                 varbinds
----                --------- -------  ---                                 --------
1567595151560645019 PE1       17.0.0.1 IF-MIB::linkUp                      IF-MIB::ifIndex.1073741824=528, IF-MIB::ifAdminStatus.1073741824=testing, IF-MIB::ifOperStatus.1073741824=up, IF-MIB::ifName.1073741824=ge-0/0/2
1567595133817560582 PE1       17.0.0.1 IF-MIB::linkDown                    IF-MIB::ifIndex.1073741824=527, IF-MIB::ifAdminStatus.1073741824=testing, IF-MIB::ifOperStatus.1073741824=down, IF-MIB::ifName.1073741824=ge-0/0/1
1567595076087076725 PE1       17.0.0.1 JUNIPER-CFGMGMT-MIB::jnxCmCfgChange JUNIPER-CFGMGMT-MIB::jnxCmCfgChgEventTime.1073741824=34:0:04:39.05, JUNIPER-CFGMGMT-MIB::jnxCmCfgChgEventDate.1073741824=2019-9-4,4:4:35.0,-7:0, JUNIPER-CFGMGMT-MIB::jnxCmCfgChgEventSource.1073741824=unknown, JUNIPER-CFGMGMT-MIB::jnxCmCfgChgEventUser.1073741824=abcdefghijklmnopqrst, JUNIPER-CFGMGMT-MIB::jnxCmCfgChgEventLog.1073741824=abcdefghijklmnopqrst, SNMPv2-MIB::snmpTrapEnterprise.0=JUNIPER-CHASSIS-DEFINES-MIB::jnxProductNameMX960
```

`Configure Custom Processing for Defined Traps:`

Custom processing is based on matching the `snmpTrapOID` of the Trap. This is configured in the section *mappings:* 
The key value in the `mappings` dictionary needs to completely match the trap "snmpTrapOID" value.
Trap information can be exported into the separate InfluxDB *measurement*. 
From the selected Trap, any *varbind OID* that match the *tags* list, will be exported to the *measurement*. 
From the selected Trap, any *varbind OID* that match the *fields* list, will be exported to the *measurement*. 

Example *mappings* configuration:
```
# Custom processing based on OID
mappings:
  IF-MIB::linkUp:
    measurement: link
    tags:
      - snmpTrapOID
      - ifIndex
      - ifName
    fields:
      - ifAdminStatus
      - ifOperStatus
  IF-MIB::linkDown:
    measurement: link
    tags:
      - snmpTrapOID
      - ifIndex
      - ifName
    fields:
      - ifAdminStatus
      - ifOperStatus
```


`Example Custom output from the database:`
```
name: link
time                host_ip  host_name ifAdminStatus ifIndex ifName   ifOperStatus   snmpTrapOID      
----                -------  --------- ------------- ------- ------   ------------   -----------      
1567595151560645019 10.0.0.1 PE1       testing       528     ge-0/0/2 up             IF-MIB::linkUp   
1567595133817560582 10.0.0.1 PE1       testing       527     ge-0/0/1 down           IF-MIB::linkDown 
1567526318214027243 10.0.0.1 PE1       testing       529     ge-0/0/3 lowerLayerDown IF-MIB::linkDown 
1567526311842142467 10.0.0.1 PE1       testing       528     ge-0/0/2 lowerLayerDown IF-MIB::linkDown 
1567526246944423884 10.0.0.1 PE1       testing       528     ge-0/0/2 lowerLayerDown IF-MIB::linkDown 
```

### 5. Run container usind docker-compose
Using docker-compose is the easiest way to run the container. The docker-compose files creates volumes for sharing the local files with the container. The sample provided includes an associated influxdB container.
In this way the container image does not need to be rebuilt every time the configuration is updated?:
Adding MIBs and changing net-snmp configuration requires a container restart. 
A Change of the script configuration file will be effective immediately.

To start the containter use *docker-compose up*:
```
# docker-compose up -d
Pulling snmptrapd-influxdb-export (audiocomp/snmptrapd-influxdb-exporter:)...
latest: Pulling from audiocomp/snmptrapd-influxdb-exporter
9d48c3bd43c5: Pull complete
c0ea575d71b9: Pull complete
0f535eceebd5: Pull complete
8a30f5893bea: Pull complete
c1d30ace7b67: Pull complete
230707bd244e: Pull complete
5c4a43cee401: Pull complete
658d73f820a7: Pull complete
2e338ad3a95f: Pull complete
551e2efe1d49: Pull complete
d91e14013992: Pull complete
07209b9f9bfb: Pull complete
Creating snmptrapd-influxdb-exporter ... done
```

To confirm the container is running use *docker ps*:
```
# docker ps
CONTAINER ID        IMAGE                                    COMMAND                  CREATED           STATUS          PORTS                              NAMES
631668ddc189        audiocomp/snmptrapd-influxdb-exporter       "snmptrapd -m ALL -f"    5 seconds ago     Up 4 seconds    162/tcp, 0.0.0.0:162->162/udp      snmptrapd-influxdb-exporter
```

NB. The Container listens on the UDP port 162 for SNMP Traps. 

The Container logs to the standard output, so you can see the logs from docker, after the first trap has been processed by using *docker logs*:
```
# docker logs snmptrapd-influxdb-exporter
2019-09-04 05:12:04,094 - snmptrapd-influxdb-exporter - INFO - config: {'logging': 'debug', 'influxdb': {'server': [{'name': 'local', 'ip': '172.17.0.1', 'port': 8086, 'db': 'snmptraps', 'user': 'juniper', 'pass': 'juniper'}]}, 'all': {'measurement': 'snmptraps', 'tags': {'host_dns': 'host_name', 'host_ip': 'host_ip', 'oid': 'oid'}}, 'mappings': {'IF-MIB::linkUp': {'measurement': 'link', 'tags': ['snmpTrapOID', 'ifIndex', 'ifName'], 'fields': ['ifAdminStatus', 'ifOperStatus']}, 'IF-MIB::linkDown': {'measurement': 'link', 'tags': ['snmpTrapOID', 'ifIndex', 'ifName'], 'fields': ['ifAdminStatus', 'ifOperStatus']}}}
2019-09-04 05:12:04,094 - snmptrapd-influxdb-exporter - DEBUG - host_dns: 10.49.170.189
2019-09-04 05:12:04,095 - snmptrapd-influxdb-exporter - DEBUG - host_ip: 10.49.170.189
2019-09-04 05:12:04,095 - snmptrapd-influxdb-exporter - DEBUG - OID: IF-MIB::linkUp
2019-09-04 05:12:04,095 - snmptrapd-influxdb-exporter - DEBUG - IF-MIB::ifIndex.1073741824 1073741824
2019-09-04 05:12:04,095 - snmptrapd-influxdb-exporter - DEBUG - IF-MIB::ifAdminStatus.1073741824 testing
2019-09-04 05:12:04,096 - snmptrapd-influxdb-exporter - DEBUG - IF-MIB::ifOperStatus.1073741824 lowerLayerDown
2019-09-04 05:12:04,096 - snmptrapd-influxdb-exporter - INFO - received trap: {'host_dns': '10.49.170.189', 'host_ip': '10.49.170.189', 'oid': 'IF-MIB::linkUp', 'sysuptime': '15:2:11:10.72', 'varbinds': ['IF-MIB::ifIndex.1073741824=1073741824', 'IF-MIB::ifAdminStatus.1073741824=testing', 'IF-MIB::ifOperStatus.1073741824=lowerLayerDown'], 'varbinds_dict': {'SNMPv2-MIB::snmpTrapOID.0': 'IF-MIB::linkUp', 'IF-MIB::ifIndex.1073741824': '1073741824', 'IF-MIB::ifAdminStatus.1073741824': 'testing', 'IF-MIB::ifOperStatus.1073741824': 'lowerLayerDown'}}
2019-09-04 05:12:04,096 - snmptrapd-influxdb-exporter - DEBUG - add oid_datapoint {'measurement': 'link', 'tags': {'host_name': '10.49.170.189', 'host_ip': '10.49.170.189', 'snmpTrapOID': 'IF-MIB::linkUp', 'ifIndex': '1073741824'}, 'fields': {'ifAdminStatus': 'testing', 'ifOperStatus': 'lowerLayerDown'}}
```

To Stop the containter use *docker-compose down*:
```
# docker-compose down
```

To Restart the containter use *docker-compose up*:
```
# docker-compose up -d
```


