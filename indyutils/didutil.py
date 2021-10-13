import json
import pprint
import logging

from typing import Tuple, Union

from indy import pool, ledger, wallet, did, anoncreds
from indy.error import IndyError, ErrorCode

pp = pprint.PrettyPrinter(indent=4)

async def create_and_store_did(seed, alias, wh) -> Union[tuple, None]:
    """
    wh: wallet handle
    did_json: did json
    return: did, verkey if error None
    """

    did_json = json.dumps({"seed": seed})

    try:
        logging.info(
            "Creating and storing did {} in wh {}".format(did_json, wh))

        d, verkey = await did.create_and_store_my_did(wh, did_json)
        metadata = json.dumps({"alias": alias})
        await did.set_did_metadata(wh, d, metadata)
        return d, verkey
    except Exception as e:
        logging.error("Can't create and store did: {}".format(did_json))
        return None


async def list_dids(wh) -> Union[list, None]:
    """
    """

    try:
        logging.info("Listing dids from wh {}".format(wh))
        return await did.list_my_dids_with_meta(wh)
    except Exception as e:
        logging.error("Can't list did from wh {}".format(wh))
        return None


async def submit_did_to_ledger(did, wh, ph) -> bool:
    """
    """

    pass
