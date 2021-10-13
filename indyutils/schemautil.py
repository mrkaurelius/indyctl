import json
import logging

from typing import Tuple, Union

from indy import pool, ledger, wallet, did, anoncreds


# TODO error handling
async def get_schema_from_ledger(schema_id:str, ph: int) -> Tuple[str, dict]:
    """"""
    logging.info("Getting schema {} from ledger".format(schema_id))
    get_schema_req = await ledger.build_get_schema_request(None, schema_id)
    resp = await ledger.submit_request(ph, get_schema_req)
    logging.debug("Schema resp {}".format(resp))
    schema_id, schema = await ledger.parse_get_schema_response(resp)
    return schema_id, schema


async def add_schema_to_ledger(submitter_did: str, name: str, version: str, attrs: str, ph: int, wh: int) -> Union[str, None]:
    """
    returns: schema_id, schema_json
    returns fetched schema
    """

    logging.debug("name {}".format(name))
    logging.debug("attrs {}".format(attrs))
    try:
        schema_id, schema_json = await anoncreds.issuer_create_schema(submitter_did, name, version, attrs)
    except Exception as e:
        logging.error("Failed to create schema")
        return None

    logging.debug("Created schema id {}".format(schema_id))
    logging.debug("Created schema json {}".format(schema_json))

    schema_response = None
    try:
        schema_request = await ledger.build_schema_request(submitter_did, schema_json)
        logging.debug("Schema request {}".format(schema_request))
    except Exception as e:
        logging.error("Failed to create schema request")
        return None

    try:
        schema_response = \
            await ledger.sign_and_submit_request(ph,
                                                 wh,
                                                 submitter_did,
                                                 schema_request)
        logging.debug("Schema response {}".format(schema_response))
    except Exception as e:
        logging.error("Failed to send submit request")
        return None

    schema_response = json.loads(schema_response)
    if schema_response['op'] == 'REJECT':
        logging.error('Schema request rejected !')
        return None
    else:
        logging.info("Schema request accepted")
        logging.debug('Schema {} added to ledger'.format(schema_id))

    # TODO error handling
    # get schema def from ledger
    schema_id, schema_json = await get_schema_from_ledger(schema_id, ph)
    logging.info("Fetched schema id {}".format(schema_id))
    logging.info("Fetched Schema json {}".format(schema_json))
    
    return schema_id, schema_json
