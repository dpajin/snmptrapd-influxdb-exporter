from copy import deepcopy
from typing import Any, Dict, List

from modules.influxdb import write_datapoints
from modules.load_config import log, snmp_config


def default_mapping_datapoint(message: Dict[str, Any]) -> Dict[str, Any]:
    varbinds = ", ".join(message['varbinds'])
    datapoint = {
        "measurement": snmp_config.default_mapping.measurement,
        "tags": {
            snmp_config.default_mapping.tags.host_dns: message['host_dns'],
            snmp_config.default_mapping.tags.host_ip: message['host_ip'],
            snmp_config.default_mapping.tags.oid: message['oid']
        },
        "fields": {
            "varbinds": varbinds
        }
    }
    log.debug(f'Add datapoint: {datapoint}')
    return datapoint


def custom_mapping_datapoint(
        message: Dict[str, Any],
        mapping: Dict[str, Any]) -> Dict[str, Any]:
    oid_datapoint = {}
    oid_datapoint['measurement'] = mapping.measurement
    oid_datapoint['tags'] = {}
    oid_datapoint['tags'].update(
        {snmp_config.default_mapping.tags.host_dns: message['host_dns']})
    oid_datapoint['tags'].update(
        {snmp_config.default_mapping.tags.host_ip: message['host_ip']})
    oid_datapoint['fields'] = {}
    for varbind in message['varbinds_dict'].keys():
        for element in mapping.tags:
            if element in varbind:
                oid_datapoint['tags'].update(
                    {element: message['varbinds_dict'][varbind]})
        for element in mapping.fields:
            if element in varbind:
                oid_datapoint['fields'].update(
                    {element: message['varbinds_dict'][varbind]})
    log.debug(f'Add oid_datapoint: {oid_datapoint}')
    return oid_datapoint


async def build_datapoints(message: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Build datapoints from Trap Message
    datapoints = []
    # Build Datapoints for default_mapping
    if snmp_config.default_mapping.permit is not None:
        for rule in snmp_config.default_mapping.permit:
            if rule in message['oid']:
                log.debug(f'Permit Rule: {rule} matches oid: {message["oid"]}')
                datapoint = default_mapping_datapoint(message)
                datapoints.append(datapoint)
    elif snmp_config.default_mapping.deny is not None:
        permit = True
        for rule in snmp_config.default_mapping.deny:
            if rule in message['oid']:
                log.debug(f'Deny Rule: {rule} matches oid: {message["oid"]}')
                permit = False
                break
        if permit:
            datapoint = default_mapping_datapoint(message)
            datapoints.append(datapoint)
    else:
        # no permit or deny rules, so permit everything
        datapoint = default_mapping_datapoint(message)
        datapoints.append(datapoint)

    # Update Datapoints for custom_mapping
    if snmp_config.custom_mappings is not None:
        if message['oid'] in snmp_config.custom_mappings:
            mapping = snmp_config.custom_mappings.get(message['oid'])
            oid_datapoint = custom_mapping_datapoint(message, mapping)
            datapoints.append(deepcopy(oid_datapoint))

    await write_datapoints(datapoints)
