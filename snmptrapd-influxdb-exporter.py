#!/usr/bin/python
import sys
import logging
import logging.handlers
import yaml
import copy
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

def get_all_traps_influx_datapoint(config, trap):
    varbinds = ", ".join(trap['varbinds'])
    datapoint = {
        "measurement" : config['all']['measurement'],
        "tags": {
            config['all']['tags'].get('host_dns', 'host_dns'): trap['host_dns'],
            config['all']['tags'].get('host_ip', 'host_ip'): trap['host_ip'],
            config['all']['tags'].get('oid', 'oid'): trap['oid']
        },
        "fields" : {
            "varbinds" : varbinds
        }
    }
    return datapoint


# logging part
logger = logging.getLogger("snmptrapd-influxdb-exporter")
logger.setLevel(logging.DEBUG)

f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

syslog_handler = logging.handlers.SysLogHandler()
syslog_handler.setFormatter(f_format)
logger.addHandler(syslog_handler)

out_handler = logging.StreamHandler(sys.stdout)
out_handler.setFormatter(f_format)
logger.addHandler(out_handler)

# Read config file
config_file = open('./config.yaml', 'r')
config = yaml.load(config_file, yaml.SafeLoader)

# adjust logging level from the config file 
numeric_level = getattr(logging, config.get("logging", "DEBUG").upper(), 10)
logger.setLevel(numeric_level)

logger.info("config: %s" % str(config))

lines = sys.stdin.readlines()

# Parsing input from snmptrapd
# parsing DNS name and IP
trap = {}
trap['host_dns'] = lines[0].strip()
socket = lines[1]
trap['host_ip'] = socket[socket.find('[') + 1:socket.find(']')]
logger.debug("host_dns: %s" % str(trap['host_dns']))
logger.debug("host_ip: %s" % str(trap['host_ip']))

# parsing SNMP stuff
trap['oid'] = None
trap['sysuptime'] = None
trap['varbinds'] = []
trap['varbinds_dict'] = {}
for line in lines[2:]:
    if trap['sysuptime'] is None:
        if "sysUpTime" in line:
            trap['sysuptime'] = line.split(" ")[1].strip()
            continue
    if trap['oid'] is None:
        if "snmpTrapOID" in line:
            varbind = line.strip().split(" ", 1)
            trap['varbinds_dict'][varbind[0]] = varbind[1]
            trap['oid'] = varbind[1].strip()
            logger.debug("OID: %s" % trap['oid'])
            continue
    trap['varbinds'].append(line.strip().replace(" ", "="))
    varbind = line.strip().split(" ", 1)
    trap['varbinds_dict'][varbind[0]] = varbind[1]
    logger.debug(line.strip())

logger.info("received trap: %s" % str(trap))

# preparing data for influxdb
# putting combined mesrsage into the one measurement for all taps
datapoints = []
if config.get('all', None) is not None:
    if config['all'].get('measurement', None) is not None:
        if config['all'].get('permit', None) is not None:
            for rule in config['all']['permit']:
                if rule in trap['oid']:
                    logger.debug("permit rule %s matching oid %s" % (rule, trap['oid']))
                    datapoints.append(get_all_traps_influx_datapoint(config, trap))
        elif config['all'].get('deny', None) is not None:
            for rule in config['all']['deny']:
                if rule in trap['oid']:
                    logger.debug("deny rule %s matching oid %s" % (rule, trap['oid']))
                    break
            else:
                # if deny rule is not match
                datapoints.append(get_all_traps_influx_datapoint(config, trap))
        else:
            # no permit or deny rules, so permit everything
            datapoints.append(get_all_traps_influx_datapoint(config, trap))
    else:
        logger.warning("configuration file missing 'all/measurement' part")
else:
    logger.warning("configuration file missing 'all' part")

# processing for each type of traps according to the mappings configuration
cfg_mappings = config.get('mappings', None)
if cfg_mappings is not None:
    mapping = cfg_mappings.get(trap['oid'], None)
    if mapping is not None:
        oid_datapoint = {}
        oid_datapoint['measurement'] = mapping['measurement']
        oid_datapoint['tags'] = {}
        oid_datapoint['tags'].update({ config['all']['tags'].get('host_dns', 'host_dns'): trap['host_dns'] })
        oid_datapoint['tags'].update({ config['all']['tags'].get('host_ip', 'host_ip'): trap['host_ip'] })
        oid_datapoint['fields'] = {}
        for varbind in trap['varbinds_dict'].keys():
            for element in mapping['tags']:
                if element in varbind:
                    oid_datapoint['tags'].update({ element : trap['varbinds_dict'][varbind] })
            for element in mapping['fields']:
                if element in varbind:
                    oid_datapoint['fields'].update({ element: trap['varbinds_dict'][varbind] })
        logger.debug("add oid_datapoint %s" % (oid_datapoint))
        datapoints.append(copy.deepcopy(oid_datapoint))
    else:
        logger.debug("configuraton no mappings for trap %s" % (trap['oid']))
else:
    logger.info("configuration file missing 'mappings' part")

# export to influxdb
if datapoints != [] and config.get('influxdb', None) is not None:
    dbclients = []
    for server in config['influxdb'].get('server', []):
        dbclient = (InfluxDBClient(url=server['url'], token=server['token'], org=server['org']), server['bucket'])
        dbclients.append(dbclient)
    if dbclients != []:
        for dbclient, bucket in dbclients:
            write_api = dbclient.write_api(write_options=SYNCHRONOUS)
            write_api.write(bucket=bucket, record=datapoints)

