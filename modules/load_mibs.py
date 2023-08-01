import os
from pysnmp.smi import builder, view, compiler
from pysnmp.smi.error import MibNotFoundError
from typing import List

from modules.load_config import log, snmp_config

mib_path: str = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'mibs')
mib_list: List[str] = snmp_config.mib_list

mibBuilder = builder.MibBuilder()
compiler.addMibCompiler(mibBuilder, sources=[f'file://{mib_path}'])
if mib_list != []:
    try:
        mibBuilder.loadModules(*mib_list)
    except MibNotFoundError as e:
        log.error(e)
mibViewController = view.MibViewController(mibBuilder)
