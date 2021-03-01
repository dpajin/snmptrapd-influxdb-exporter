# snmptrapd-influxdb-exporter

This is SNMP Trap collector based on *net-snmp* package *snmptrapd*, which then provides the export to InfluxDB using custom Python script.

## How to use it and how it works

#### clone the repo
Clone the repo and make mibs directory
```
git clone https://github.com/audiocomp/snmptrapd-influxdb-exporter.git
cd snmptrapd-influxdb-exporter
mkdir mibs
```

### add SNMP MIBs
Any SNMP MIB files that should be used for SNMP Traps processing should be places in the directory `mibs/`. The content of this directory will be copied to the docker container in the `/usr/share/mibs/`, according to the statement in the `Dockerfile`.

To add *Juniper* SNMP MIBs in the `mibs` directory, use the following:
```
wget https://www.juniper.net/documentation/software/junos/junos192/juniper-mibs-19.2R1.8.tgz
tar -xvf juniper-mibs-19.2R1.8.tgz -C mibs
rm -f juniper-mibs-19.2R1.8.tgz
ls -al mibs/
```

In the configuration file located at `net-snmp/snmp.conf` is the *net-snmp* configuration. This file needs to have specified which directories will be used to load SNMP MIB files.  Any directory should be also listed in the `net-snmp/snmp.conf` similarly as those already listed:
```
mibdirs +/usr/share/mibs/JuniperMibs
mibdirs +/usr/share/mibs/StandardMibs
```

### snmptrapd
The *snmptrapd* has an option to execute custom script upon receiving of a SNMP Trap. It will provide data from the parsed SNMP Trap as a standard input into the custom script. 
This is controlled by configuration file located in `net-snmp/snmptrapd.conf`. The following two lines are important from this configuration file:
```
authCommunity execute public
traphandle default python /snmptrapd-influxdb-exporter.py
```
The first line defines what will be the action for the community used. The default accepted community is `public`. If it is needed to accept more communities, those should be configured here. This is default configuration for SNMPv2c.

If receiving of SNMPv3 Traps is needed, that should be configured in this file as well. Please consult *net-snmp* and *snmptrapd* documentation on how to configure SNMPv3 traps. 

The second line defines how  received SNMP Traps will be handled. This line specifies that the Python script   `snmptrapd-influxdb-exporter.py`, located in the `/` directory will be executed for each SNMP Trap.

### SNMP traps processing configuration
SNMP Traps processing is done with `snmptrapd-influxdb-exporter.py` script. The script's processing can be configured using `config.yaml` file.
The configuration file has the following sections:

#### tune logging level:
```
logging: debug
```

#### destination InfluxDB servers configuration:
Change the InfluxDB server IP address and tune the database access parameters. The database configured should already exist on the InfluxDB server.
There can be more than one server configured.
```
influxdb:
  server:
    - name: local
      url: http://172.17.0.2:8086
      org: snmptraps
      token: influx-snmptraps
      bucket: snmptraps
```


#### All traps processing configuration
This section defines how all the traps will be processed. All traps will be exported to the same influxb "measurement", which name is configured in this section.
InfluxDB measurement tags can be customized here, where measurement field is called varbinds. It consist of comma-sepratated list of varbinds in the following format: `oid1=value1, oid2=value2, ...`

There is a possibility to make permit and deny lists to filter certain Traps based on snmpTrapOID value. The *permit* list takes precedence, so if it is configured, only Traps matched with entries in the list will be accepted and all other will be denied. If *permit* list is not configured, but *deny* list exists, it will accept all Traps except those configured in the *deny* list. If none of the lists are configured, it will accept all SNMP Traps.

Example configuration:
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
  deny:
    - JUNIPER-CFGMGMT-MIB::jnxCmCfgChange
```

Example output from the database:
```
root@bb314482a0b3:/# influx
Connected to http://localhost:8086 version 2.0.4
InfluxDB shell version: 2.0.4
> use snmptraps;
Using database snmptraps
> SELECT host_name, host_ip, oid, varbinds FROM "snmptraps".."snmptraps" WHERE time > now() - 7d order by time desc limit 10
name: snmptraps
time                host_name host_ip  oid                                 varbinds
----                --------- -------  ---                                 --------
1567595151560645019 PE1       17.0.0.1 IF-MIB::linkUp                      IF-MIB::ifIndex.1073741824=528, IF-MIB::ifAdminStatus.1073741824=testing, IF-MIB::ifOperStatus.1073741824=up, IF-MIB::ifName.1073741824=ge-0/0/2
1567595133817560582 PE1       17.0.0.1 IF-MIB::linkDown                    IF-MIB::ifIndex.1073741824=527, IF-MIB::ifAdminStatus.1073741824=testing, IF-MIB::ifOperStatus.1073741824=down, IF-MIB::ifName.1073741824=ge-0/0/1
1567595076087076725 PE1       17.0.0.1 JUNIPER-CFGMGMT-MIB::jnxCmCfgChange JUNIPER-CFGMGMT-MIB::jnxCmCfgChgEventTime.1073741824=34:0:04:39.05, JUNIPER-CFGMGMT-MIB::jnxCmCfgChgEventDate.1073741824=2019-9-4,4:4:35.0,-7:0, JUNIPER-CFGMGMT-MIB::jnxCmCfgChgEventSource.1073741824=unknown, JUNIPER-CFGMGMT-MIB::jnxCmCfgChgEventUser.1073741824=abcdefghijklmnopqrst, JUNIPER-CFGMGMT-MIB::jnxCmCfgChgEventLog.1073741824=abcdefghijklmnopqrst, SNMPv2-MIB::snmpTrapEnterprise.0=JUNIPER-CHASSIS-DEFINES-MIB::jnxProductNameMX960
```

#### Special processing of certain Traps:

Example configuration is provided below:

```
# Special processing based on OID
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
Special processing is based on mathing `snmpTrapOID` of the Trap. This is configured in the section mappings. 
The key value in the `mappings` dictionary needs to completely match the trap "snmpTrapOID" value.
The specific processing for the trap can be configured here. Trap information can be exported into the separate InfluxDB *measurement*. 
From the selected Trap, any *varbind OID* that match the *tags* list, will be exported to the *measurement*. 
From the selected Trap, any *varbind OID* that match the *fields* list, will be exported to the *measurement*. 

Example from the database:

```
> SELECT * FROM "snmptraps".."link" WHERE time > now() - 7d order by time desc limit 5
name: link
time                host_ip  host_name ifAdminStatus ifIndex ifName   ifOperStatus   snmpTrapOID      
----                -------  --------- ------------- ------- ------   ------------   -----------      
1567595151560645019 10.0.0.1 PE1       testing       528     ge-0/0/2 up             IF-MIB::linkUp   
1567595133817560582 10.0.0.1 PE1       testing       527     ge-0/0/1 down           IF-MIB::linkDown 
1567526318214027243 10.0.0.1 PE1       testing       529     ge-0/0/3 lowerLayerDown IF-MIB::linkDown 
1567526311842142467 10.0.0.1 PE1       testing       528     ge-0/0/2 lowerLayerDown IF-MIB::linkDown 
1567526246944423884 10.0.0.1 PE1       testing       528     ge-0/0/2 lowerLayerDown IF-MIB::linkDown 
```

### Run container usind docker-compose
Using docker-compose is the easiest way to run the container. The docker-compose files creates volumes for sharing the local files with the container.
In this way you don't need to rebuild the container image every time you change the configuration, but just to restart it. 
Adding MIBs and changing net-snmp configuration requires container restart. Change of the script configuration file will be effective immediately.

To re/start the containter:
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

Check if the container is running

```
# docker ps
CONTAINER ID        IMAGE                                    COMMAND                  CREATED           STATUS          PORTS                              NAMES
631668ddc189        audiocomp/snmptrapd-influxdb-exporter       "snmptrapd -m ALL -f"    5 seconds ago     Up 4 seconds    162/tcp, 0.0.0.0:162->162/udp      snmptrapd-influxdb-exporter
```

Container listens on the UDP port 162 for SNMP Traps. 

Container logs to the standard output, so you can see the logs from docker, once you receive the first trap:

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

Stop the containter:
```
# docker-compose down
```


