import logging
import sys
from time import gmtime
from typing import Optional

import yaml  # type: ignore
from models.config import Config

FILENAME: str = "config.yaml"
log_map = {
    "CRITICAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "INFO": 20,
    "DEBUG": 10
}

# Configure Logging
log = logging.getLogger("snmptrapd-influxdb-exporter")
formatter = logging.Formatter(
    "%(levelname)s | %(asctime)s | %(name)s | %(message)s"
)
formatter.converter = gmtime
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
log.addHandler(console_handler)
log.setLevel(40)

snmp_config: Optional[Config] = None
try:
    with open(FILENAME, "r") as config_file:
        contents = config_file.read()
        if contents:
            unvalidated_config = yaml.load(contents, Loader=yaml.Loader)
            log.debug(f"Config File: {unvalidated_config}")
        else:
            log.error("Unable to load config.yaml")
except FileNotFoundError:
    log.error("config.yaml not found")
except (KeyError, ValueError):
    log.error("Unable to load config.yaml")
if unvalidated_config is not None:
    try:
        snmp_config = Config(**unvalidated_config)
    except ValueError as e:
        log.error(f"Config File Validation Failed: {e}")
else:
    log.error("Unable to Validate Config File")

if snmp_config is not None:
    log_level = snmp_config.logging.value
    if log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        log.setLevel(int(log_map[log_level]))

log.debug(f"Processed snmp_conifg: {snmp_config}")
