from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel


class LogLevel(Enum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class AuthProtocol(Enum):
    usmHMACMD5AuthProtocol = "md5"
    usmHMACSHAAuthProtocol = "sha"
    usmHMAC128SHA224AuthProtocol = "sha128"
    usmHMAC192SHA256AuthProtocol = "sha192"
    usmHMAC256SHA384AuthProtocol = "sha256"
    usmHMAC384SHA512AuthProtocol = "sha512"
    usmNoAuthProtocol = "none"


class PrivProtocol(Enum):
    usmAesCfb128Protocol = "aes128"
    usmAesCfb192Protocol = "aes192"
    usmAesCfb256Protocol = "aes256"
    usmDESPrivProtocol = "des"
    usm3DESEDEPrivProtocol = "3des"
    usmAesBlumenthalCfb192Protocol = "aes192Blumenthal"
    usmAesBlumenthalCfb256Protocol = "aes256Blumenthal"
    usmNoPrivProtocol = "none"


class Server(BaseModel):
    name: str
    url: str
    org: str
    token: str
    bucket: str


class Influxdb(BaseModel):
    server: List[Server]


class Tags(BaseModel):
    host_dns: str
    host_ip: str
    oid: str


class DefaultMapping(BaseModel):
    measurement: str
    tags: Tags
    permit: Optional[List[str]] = None
    deny: Optional[List[str]] = None


class CustomMapping(BaseModel):
    measurement: str
    tags: List[str]
    fields: List[str]


class User(BaseModel):
    user: str
    auth_protocol: AuthProtocol
    auth_key: Optional[str] = None
    priv_protocol: PrivProtocol
    priv_key: Optional[str] = None
    engine_id: Optional[str] = None


class SnmpV3(BaseModel):
    engine_id: str
    users: List[User]


class SnmpV2(BaseModel):
    community: str
    description: str


class Config(BaseModel):
    logging: LogLevel
    influxdb: Influxdb
    default_mapping: DefaultMapping
    custom_mappings: Optional[Dict[str, CustomMapping]]
    mib_list: List[str]
    snmpv2: Optional[List[SnmpV2]]
    snmpv3: Optional[SnmpV3]
