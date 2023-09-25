import asyncio

from modules.datapoints import build_datapoints
from modules.load_config import log, snmp_config
from modules.load_mibs import mibViewController
from pysnmp.carrier.asyncio.dgram import udp
from pysnmp.entity import config, engine
from pysnmp.entity.rfc3413 import ntfrcv
from pysnmp.proto.api import v2c
from pysnmp.smi import rfc1902

authProtocol = {
    "usmHMACMD5AuthProtocol": config.usmHMACMD5AuthProtocol,
    "usmHMACSHAAuthProtocol": config.usmHMACSHAAuthProtocol,
    "usmHMAC128SHA224AuthProtocol": config.usmHMAC128SHA224AuthProtocol,
    "usmHMAC192SHA256AuthProtocol": config.usmHMAC192SHA256AuthProtocol,
    "usmHMAC256SHA384AuthProtocol": config.usmHMAC256SHA384AuthProtocol,
    "usmHMAC384SHA512AuthProtocol": config.usmHMAC384SHA512AuthProtocol,
    "usmAesCfb128Protocol": config.usmAesCfb128Protocol,
    "usmAesCfb256Protocol": config.usmAesCfb256Protocol,
    "usmAesCfb192Protocol": config.usmAesCfb192Protocol,
    "usmDESPrivProtocol": config.usmDESPrivProtocol,
    "usm3DESEDEPrivProtocol": config.usm3DESEDEPrivProtocol,
    "usmAesBlumenthalCfb192Protocol": config.usmAesBlumenthalCfb192Protocol,
    "usmAesBlumenthalCfb256Protocol": config.usmAesBlumenthalCfb256Protocol,
    "usmNoAuthProtocol": config.usmNoAuthProtocol,
    "usmNoPrivProtocol": config.usmNoPrivProtocol,
}


def snmp_engine():
    # Create SNMP engine with autogenernated engineID and pre-bound
    # to socket transport dispatcher
    snmpEngine = engine.SnmpEngine(
        snmpEngineID=v2c.OctetString(hexValue=snmp_config.snmpv3.engine_id)
    )

    # Transport setup
    # UDP over IPv4, first listening interface/port
    config.addTransport(
        snmpEngine,
        udp.domainName + (1,),
        udp.UdpTransport().openServerMode(("0.0.0.0", 162)),
    )

    # SNMPv1/2c setup
    # SecurityName <-> CommunityName mapping
    if snmp_config.snmpv2 is not None:
        for entry in snmp_config.snmpv2:
            config.addV1System(snmpEngine, entry.description, entry.community)

    # SNMP v3 setup
    if snmp_config.snmpv3.users is not None:
        for user in snmp_config.snmpv3.users:
            if user.engine_id is not None:
                user.engine_id = v2c.OctetString(hexValue=user.engine_id)
            config.addV3User(
                snmpEngine,
                userName=user.user,
                authKey=user.auth_key,
                privKey=user.priv_key,
                authProtocol=authProtocol.get(
                    user.auth_protocol.name, config.usmNoAuthProtocol
                ),
                privProtocol=authProtocol.get(
                    user.priv_protocol.name, config.usmNoPrivProtocol
                ),
                securityEngineId=user.engine_id,
            )

    # Callback function for receiving notifications
    def cbFun(
        snmpEngine,
        stateReference,
        contextEngineId,
        contextName,
        varBinds,
        cbCtx,
    ):
        _, tAddress = snmpEngine.msgAndPduDsp.getTransportInfo(stateReference)
        message = {}
        message["host_dns"] = tAddress[0].strip()
        message["host_ip"] = tAddress[0].strip()
        message["oid"] = None
        message["sysuptime"] = None
        message["varbinds"] = []
        message["varbinds_dict"] = {}
        for oid, val in varBinds:
            varBind = str(
                rfc1902.ObjectType(
                    rfc1902.ObjectIdentity(oid), val
                ).resolveWithMib(mibViewController)
            )
            if "sysUpTime" in varBind:
                message["uptime"] = varBind.split(" = ")[1].strip()
            elif "snmpTrapOID" in varBind:
                if message["oid"] is None:
                    message["oid"] = varBind.split(" = ")[1].strip()
            else:
                message["varbinds"].append(varBind)
                if len(varBind.split(" = ")) > 1:
                    message["varbinds_dict"][
                        varBind.split(" = ")[0].strip()
                    ] = varBind.split(" = ")[1].strip()
        log.info(
            f"Trap From: {tAddress}, EngineId {contextEngineId.prettyPrint()}"
        )
        log.debug(f"Context Name: {contextName}, cbCtx: {cbCtx}")
        log.debug(f"Trap Detail: {message}")
        asyncio.create_task(build_datapoints(message))

    # Register SNMP Application at the SNMP engine
    ntfrcv.NotificationReceiver(snmpEngine, cbFun)
    snmpEngine.transportDispatcher.jobStarted(1)
    try:
        log.error("Trap Receiver started on port 162. Press Ctrl-c to quit.")
        snmpEngine.transportDispatcher.runDispatcher()
        ntfrcv.NotificationReceiver(snmpEngine, cbFun)
    except KeyboardInterrupt:
        log.error("Ctrl-c Pressed. Trap Receiver Stopped")
    finally:
        snmpEngine.transportDispatcher.closeDispatcher()


def main():
    snmp_engine()


if __name__ == "__main__":
    main()
