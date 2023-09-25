from typing import Any, Dict, List

from aiohttp.client_exceptions import ClientError
from aiohttp_retry import ExponentialRetry, RetryClient
from asyncio.exceptions import TimeoutError
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from modules.load_config import log, snmp_config


async def write_datapoints(datapoints: List[Dict[str, Any]]):
    # export to influxdb
    if datapoints != [] and snmp_config.influxdb != []:
        dbclients = []
        buckets = []
        retry_options = ExponentialRetry(
            attempts=5,
            start_timeout=5.0,
            exceptions=[ClientError, TimeoutError]
        )
        for server in snmp_config.influxdb.server:
            dbclient = InfluxDBClientAsync(
                url=server.url,
                token=server.token,
                org=server.org,
                verify_ssl=False,
                client_session_type=RetryClient,
                client_session_kwargs={"retry_options": retry_options},
            )
            bucket = server.bucket
            dbclients.append(dbclient)
            buckets.append(bucket)
        if dbclients != []:
            for dbclient, bucket in zip(dbclients, buckets):
                async with dbclient as client:
                    write_api = client.write_api()
                    try:
                        await write_api.write(bucket=bucket, record=datapoints)
                    except ClientError as e:
                        log.error(f"HTTP Error writing to influx: {e}")
                    except TimeoutError as e:
                        log.error(f"AsyncIo Error writing to influx: {e}")
