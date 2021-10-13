import pprint
import logging
import json

from typing import Tuple

from indy import pool, ledger, wallet, did, anoncreds
from indy.error import IndyError, ErrorCode


async def list_creds(wh):
    return await anoncreds.prover_get_credentials(wh, "{}")


async def get_cred_def_from_ledger(cred_def_id: str, ph) -> Tuple[str, str]:
    """"""
    logging.info("Getting cred {} from ledger".format(cred_def_id))
    get_cred_req = await ledger.build_get_cred_def_request(None, cred_def_id)
    resp = await ledger.submit_request(ph, get_cred_req)
    logging.debug("Cred def resp {}".format(resp))
    cred_def_id, cred_def_json = await ledger.parse_get_cred_def_response(resp)
    return cred_def_id, cred_def_json


async def add_credential_to_ledger_and_wallet(sender_did: str, wh: int, ph: int,
                                              schema_id: str, config: str, tag="TAG1", type='CL') -> Tuple[str, str]:
    """
    returns cred_def_id, cred_def_json
    """
    # TODO make similar log pattern with add schema

    # get schema data from ledger
    schema_req = await ledger.build_get_schema_request(None, schema_id)
    schema_response = await ledger.sign_and_submit_request(ph, wh, sender_did, schema_req)
    schema_id, schema_json = await ledger.parse_get_schema_response(schema_response)

    try:
        cred_def_id, cred_def_json = await anoncreds.issuer_create_and_store_credential_def(wh,
                                                                                            sender_did,
                                                                                            schema_json,
                                                                                            tag,
                                                                                            type,
                                                                                            config)
    except Exception as e:
        logging.error("Failed to create cred")

    logging.info("cred_def_id: {}".format(cred_def_id))
    logging.debug("cred_def_json: {}".format(cred_def_json))

    cred_def_resp = None
    try:
        cred_def_req = await ledger.build_cred_def_request(sender_did, cred_def_json)
    except Exception as e:
        logging.error("Failed to create cred def request")
        return None

    try:
        cred_def_req = await ledger.build_cred_def_request(sender_did, cred_def_json)
    except Exception as e:
        logging.error("Failed to create cred def request")
        return None

    try:
        cred_def_resp = await ledger.sign_and_submit_request(ph,
                                                            wh,
                                                            sender_did,
                                                            cred_def_req)
    except Exception as e:
        logging.error("Failed to sign and submit credentia request")
        return None

    cred_def_resp = json.loads(cred_def_resp)
    if cred_def_resp['op'] == 'REJECT':
        logging.error('Cred def request rejected !')
        return None
    else:
        logging.info('Cred def request accepted')
        logging.info('Cred def {} added to ledger'.format(cred_def_id))

    # TODO error handling
    # get cred def from ledger
    cred_def_id, cred_def_json = await get_cred_def_from_ledger(cred_def_id, ph)
    logging.info("Fetched cred def id {}".format(cred_def_id))
    logging.debug("Fetched cred def json {}".format(cred_def_json))

    return cred_def_id, cred_def_json
