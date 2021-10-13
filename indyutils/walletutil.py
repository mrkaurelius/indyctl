import pprint
import logging
import json
import os
import shutil
from typing import Tuple, Union

from indy import wallet
from indy.error import IndyError, ErrorCode

async def open_wallet(id, key) -> Union[int, None]:
    """
    :param id: wallet config id
    :param key: wallet cred key
    :returns wh if error None
    """

    config = json.dumps({"id": id})
    creds = json.dumps({"key": key})

    try:
        logging.info("Trying to open wallet with conf {} creds {}".format(config, creds))
        return await wallet.open_wallet(config, creds)
    except Exception as e:
        logging.error("Can't open wallet")
        return False

async def create_wallet(id, key, del_if_present=True) -> bool:
    """
    util func does json conv for indy, all optional parameters are None
    :param id: wallet config id
    :param key: wallet cred key
    """

    if del_if_present:
        wallet_path = os.path.expanduser("~/.indy_client/wallet/" + id)
        if os.path.isdir(wallet_path):
            logging.info("Deleting old wallet {}".format(id))
            shutil.rmtree(wallet_path)
    else:
        logging.info("Preserving old wallet {}".format(id))
        return True

    config = json.dumps({"id": id})
    creds = json.dumps({"key": key})

    try:
        logging.info("Creating new wallet conf {} creds {}".format(config, creds))
        await wallet.create_wallet(config, creds)
        return True
    except Exception as e:
        logging.error("Can't create wallet")
        return False