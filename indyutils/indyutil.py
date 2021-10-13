import json
import logging
import json

from os import environ
from pathlib import Path
from tempfile import gettempdir

from indy import pool, ledger, wallet, did
from indy.error import IndyError
from .pool import PROTOCOL_VERSION # daha akillica olabilir miydi ?

# FIXME cuzdani ve poolun olup olmadigini kontrol et
# FIXME eger hata olursa none don
# FIXME REFACTOR indy config yok
async def start_indy(indy_config, dwallet='steward1', dpool='sandbox'):
    """
    poola baglanir, walleti acar, handle leriniri return eder
    indy_config: indy_config
    dwallet: default wallet
    dpool: default pool

    :return: pool_handle, wallet_handle
    """

    pool_name = indy_config["pools"][dpool]["poolName"]
    wallet_config = indy_config["wallets"][dwallet]["walletConfig"]
    wallet_credential = indy_config["wallets"][dwallet]["walletCredentials"]

    # logging.info("{}, {}".format(wallet_config, wallet_credential))

    await pool.set_protocol_version(PROTOCOL_VERSION)
    wallet_handle, pool_handle = None, None
    try:
        pool_handle = await pool.open_pool_ledger(config_name=pool_name, config=None)
        wallet_handle = await wallet.open_wallet(json.dumps(wallet_config), json.dumps(wallet_credential))
    except IndyError as e:
        logging.error(e.message)

    return int(pool_handle), int(wallet_handle)


async def stop_indy(pool_handle, wallet_handle):
    """
    pool'u ve wallet'i gracefully sekilde kapatir.
    """

    try:
        logging.info("Stopping indy, closing wallet and pool")
        await wallet.close_wallet(wallet_handle)
        await pool.close_pool_ledger(pool_handle)
    except IndyError as e:
        logging.error("Error occured: {}".format(e.message))
