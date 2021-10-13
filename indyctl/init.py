# TODO bir suru map olusturmaya gerek yok *_add_resource yerinde bu yapilabilirdi

import asyncio
from ctypes import create_string_buffer
import json
import logging
from pathlib import Path
import yaml

from indy import pool, wallet
from indyctl.config import IndyctlConfig
from indyutils import didutil, poolutil, schemautil, walletutil
from os.path import expanduser, isdir
from typing import Tuple

from indyutils.credutil import add_credential_to_ledger_and_wallet, get_cred_def_from_ledger


class ResourceHandler:
    def __init__(self, config: IndyctlConfig) -> None:
        self.config = config
        self.ph = None

    # init ler async wrapperi 

    def init_didwallet_resources(self):
        logging.info("Initting didwallet resources")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__init_didwallet())

    def init_pool_resources(self):
        logging.info("Initting pool resources")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__init_pool())

    def init_schemacred_resources(self):
        logging.info("Initting schemacred resources")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.open_pool())
        loop.run_until_complete(self.__init_schemacred())


    def init_all_resources(self):
        logging.info("Initting all resources")
        loop = asyncio.get_event_loop()
        # Init didwallet
        loop.run_until_complete(self.__init_didwallet())
        loop.run_until_complete(self.__init_pool())
        loop.run_until_complete(self.open_pool())
        loop.run_until_complete(self.__init_schemacred())


    async def open_pool(self):
        """"""

        # TODO pool handle yi logla
        logging.info("Trying to open pool ledger")
        try:
            await pool.set_protocol_version(2)
            self.ph = await pool.open_pool_ledger(config_name="sandbox_docker", config=None)
            logging.info("Pool handle {}".format(self.ph))
        except Exception as e:
            logging.error("Failed to open pool ledger, exiting")
            exit(1)


    async def __init_didwallet(self):
        """"""

        dids = self.config.dids
        wallets = self.config.wallets

        w_handles = {}

        for w in wallets:
            logging.info("Creating wallet {}".format(w))
            id = wallets[w]["id"]
            key = wallets[w]["key"]
            iscreated = await walletutil.create_wallet(id, key, del_if_present=True)
            if not iscreated:
                logging.error("Can't create wallet {}, exiting".format(w))
                exit(1) 

            # add open wallet and add wh to w_handles
            wh = await walletutil.open_wallet(id, key)
            if wh is None:
                logging.error("Can't open wallet {}, exiting".format(w))
                exit(1) 

            w_handles[w] = wh

        logging.info("w_handles {}".format(w_handles))

        # didleri olustur ve dogru walletlere ekle
        for d in dids:
            logging.info("Searching wallet for, did {}".format(dids[d]))
            for w in wallets:
                if d in wallets[w]["dids"]:
                    logging.info(
                        "Creating did {} and adding to wallet {}".format(d, w))
                    wh = w_handles[w]
                    seed = dids[d]["seed"]
                    # d as did alias
                    ret = await didutil.create_and_store_did(seed, d, wh)
                    if ret is None:
                        logging.error(
                            "Could not create and store did wh {} seed {}".format(wh, seed))

        for w, wh in w_handles.items():
            fetched_dids = await didutil.list_dids(wh)
            logging.info("Fetched dids {} from wh {}".format(fetched_dids, wh))
            await wallet.close_wallet(wh)


    async def __init_schemacred(self):
        """"""

        ph = self.ph
        dids = self.config.dids
        wallets = self.config.wallets
        schemas = self.config.schemas
        creds = self.config.creds

        wid_wh_map = await build_wallet_id_wh_map(wallets)
        did_alias_wid_map = build_did_alias_wallet_id_map(
            wallets)  # did alias => wallet id map
        did_wh_map = build_did_wh_map(did_alias_wid_map, wid_wh_map)
        did_alias_did_map = await build_did_alias_did_map(wid_wh_map)  # wid => wh
        schema_alias_did_alias_map = build_schema_alias_did_alias_map(schemas)

        # cred (alias ?) => schema alias => did alias => did => wid => wh
        logging.info("did alias => wid map {}".format(did_alias_wid_map))
        logging.info("wallet id => wh map {}".format(wid_wh_map))
        logging.info("did alias => did map {}".format(did_alias_did_map))
        logging.info("schema alias => did alias map {}".format( schema_alias_did_alias_map))
        logging.info("did => wh map {}".format(did_wh_map))

        await self.__add_schema_resources_to_ledger(schemas, did_alias_did_map, did_wh_map, ph)
        await self.__add_cred_resources_to_ledger(creds, did_alias_did_map, did_wh_map, ph)

        logging.info("Closing wallet, pool handles")
        for wid, wh in wid_wh_map.items():
            await wallet.close_wallet(wh)

        await pool.close_pool_ledger(ph)


    async def __init_pool(self):
        """"""

        pools = self.config.pools
        for p in pools:
            config_name = pools[p]["config_name"]
            genesis_txn = pools[p]["genesis_txn"]
            logging.info("Creating pool {}".format(config_name))
            iscreated = await poolutil.create_pool_config(config_name, genesis_txn)
            if not iscreated:
                logging.error( "Pool {} could not created, exiting".format(config_name)) 
                exit(1)

    async def __add_cred_resources_to_ledger(self, creds: dict, did_alias_did_map: dict, did_wh_map: dict, ph: int):
        """"""
        
        # FIXME wrong nomenclature, cred_def instead cred
        logging.info("Adding cred resources to ledger, wallet")

        cred_id_def_map = {}
        schema_name_id_map = {}

        # fetch schema ids from file
        with open(self.config.created_schemas_file, "r") as f:
            schemas = json.load(f)
            schema_ids = list(schemas.keys())
            if len(schema_ids) == 0: return # schema eklenememis

        # build map
        for schema in schema_ids:
            schema_name_id_map[schema.split(":")[2]] = schema

        for cred in creds:
            cred_schema_name = creds[cred]["schema"]
            cred_submitter_did_alias = creds[cred]["did"]
            cred_type = creds[cred]["tag"]
            cred_tag = creds[cred]["type"]
            cred_submitter_did = did_alias_did_map[cred_submitter_did_alias]
            cred_submitter_wh = did_wh_map[cred_submitter_did_alias]
            cred_config = json.dumps(creds[cred]["config"])
            cred_schema_id = schema_name_id_map[cred_schema_name]

            logging.info("Adding cred {} {} to ledger, wallet".format(cred_schema_id, cred_submitter_did))
            logging.debug("cred submitter alias {}".format( cred_submitter_did_alias))
            logging.debug("cred submitter did {}".format(cred_submitter_did))
            logging.debug("cred tag did {}".format(cred_tag))
            logging.debug("cred type did {}".format(cred_type))
            logging.debug("cred schema id {}".format(cred_schema_id))

            # TODO creds.json yoksa olustur
            ret = await add_credential_to_ledger_and_wallet(cred_submitter_did, cred_submitter_wh, ph, cred_schema_id, cred_config)
            if ret is not None:
                cred_def_id, cred_def_json = ret
                cred_id_def_map[cred_def_id] = json.loads(cred_def_json)

            logging.info("Writing added creds to craeted dir")

            created_creds = None           
            with open(self.config.created_creds_file, "r") as f:
                created_creds = json.load(f)
                logging.info("Created creds {}".format(created_creds))

                for new_cred_id, new_cred_json in cred_id_def_map.items():
                    if new_cred_id not in created_creds:
                        created_creds[new_cred_id] = new_cred_json

            with open(self.config.created_creds_file, "w") as f:
                json.dump(created_creds, f, indent=4)
                

    async def __add_schema_resources_to_ledger(self, schemas: dict, did_alias_did_map: dict, did_wh_map,  ph: int):
        """"""
        # TODO proper logging

        logging.info("Adding schema resources to ledger")
        schema_id_def_map = {}

        for s in schemas:
            # TODO 
            schema_submitter_alias = str(schemas[s]["did"])
            name = str(schemas[s]["name"])
            version = str(schemas[s]["version"])
            attrs = json.dumps(schemas[s]["attributes"])
            submitter_did = did_alias_did_map[schema_submitter_alias]
            wh = did_wh_map[schema_submitter_alias]

            logging.info("Adding schema {} to ledger".format(name))
            # add schmea to ledger
            ret = await schemautil.add_schema_to_ledger(submitter_did, name, version, attrs, ph, wh)
            if ret is not None:
                schema_id, schema_json = ret
                schema_id_def_map[schema_id] = json.loads(schema_json)

        logging.info("Added schemas {}".format(json.dumps(schema_id_def_map, indent=4)))
        logging.info("Writing added schemas to created dir")

        # TODO schema.json yoksa olustur
        # once oku, schema id varmi yokmu bak varsa ekleme yoksa ekle
        created_schemas = None
        with open(self.config.created_schemas_file, "r") as f:
            created_schemas = json.load(f)
            logging.info("Created schemas {}".format(created_schemas))

            for new_schema_id, new_schema_json in schema_id_def_map.items():
                if new_schema_id not in created_schemas:
                    created_schemas[new_schema_id] = new_schema_json

        with open(self.config.created_schemas_file, "w") as f:
                json.dump(created_schemas, f, indent=4)




def build_did_wh_map(did_wid_map: dict, wid_wh_map: dict) -> dict:
    """
    """

    did_wh_map = {}
    for d, wid in did_wid_map.items():
        did_wh_map[d] = wid_wh_map[wid]

    return did_wh_map


def build_schema_alias_did_alias_map(schemas: dict) -> dict:
    """
    """

    schema_did_alias_map = {}
    for schema_alias, schema in schemas.items():
        did_alias = schema['did']
        schema_did_alias_map[schema_alias] = did_alias

    return schema_did_alias_map


# her alias'in bir did'i olacak sekilde
async def build_did_alias_did_map(wallet_wh_map: dict):
    """
    """

    alias_did_map = {}

    for wid, wh in wallet_wh_map.items():  # bu akillica bir haraket
        did_list = json.loads(await didutil.list_dids(wh))
        for d in did_list:
            alias = json.loads(d["metadata"])["alias"]
            alias_did_map[alias] = d['did']

    return alias_did_map


async def build_wallet_id_wh_map(wallets: dict) -> dict:
    """
    """

    wid_wh_map = {}
    for wid in wallets:
        wkey = wallets[wid]["key"]  # wallet key
        wh = await walletutil.open_wallet(wid, wkey)
        wid_wh_map[wid] = wh

    return wid_wh_map


# bir did birden fazla wallete olmamali seklinde calisir
def build_did_alias_wallet_id_map(wallets: dict) -> dict:
    """
    """

    did_wid_map = {}

    for wid in wallets:
        for d in wallets[wid]["dids"]:
            did_wid_map[d] = wid

    return did_wid_map
