import json
import logging
import json
import os
import shutil

from pathlib import Path
from tempfile import gettempdir

from indy import pool, ledger, wallet, did

PROTOCOL_VERSION = 2


async def create_pool_config(pool_config_name, genesis_txn, del_if_present=True) -> bool:
    """
    """

    if del_if_present:
        pool_path = os.path.expanduser(
            "~/.indy_client/pool/" + pool_config_name)
        if os.path.isdir(pool_path):
            logging.info(
                "Deleting old pool config {}".format(pool_config_name))
            shutil.rmtree(pool_path)

    genesis_dir = Path("~/.indy_client/genesis_txns").expanduser()

    if not Path.is_dir(genesis_dir):
        Path.mkdir(genesis_dir)

    # ~/.indy_client de bu poolname e sahip pool config var ise sil

    # TODO os kullanilan yerleri pathlibe cevir
    genesis_fp = genesis_dir / "{}_genesis.tx".format(pool_config_name)
    logging.info("Genesis fp {}".format(genesis_fp))

    with open(genesis_fp, "w") as f:
        f.writelines(genesis_txn)

    pool_config = json.dumps({'genesis_txn': str(genesis_fp)})
    logging.info("pool_config {}".format(pool_config))

    try:
        logging.info("Creating pool ledger config {}".format(pool_config_name))
        await pool.create_pool_ledger_config(pool_config_name, pool_config)
        return True
    except Exception as e:
        logging.error(
            "Could not create pool ledger config {} ".format(pool_config_name))
        return False
