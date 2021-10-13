import logging
import yaml
import configparser

from pathlib import Path

class IndyctlConfig:

    def __init__(self, indyctl_dir: Path) -> None:
        logging.getLogger().setLevel(logging.root.level)

        logging.info("Setting indctl config from {}".format(indyctl_dir.expanduser()))

        indyctl_dir = indyctl_dir.expanduser()
        if not indyctl_dir.is_dir():
            logging.error("Cant find indyctl dir {}, exiting".format(indyctl_dir))
            exit(1)
        else:
            self.indyctl_dir = indyctl_dir
            
        resources_dir = indyctl_dir / "resources"
        if not resources_dir.is_dir():
            logging.error("Cant find resources in {}, exiting".format(indyctl_dir))
            exit(1)
        else:
            self.resource_dir = resources_dir

        indyctl_config_file = indyctl_dir / "indyctl.cfg"
        if not indyctl_config_file.is_file():
            logging.error("Cant find indyctl.cfg in {}, exiting".format(indyctl_dir))
            exit(1)
        else:
            self.indctl_config_file = indyctl_config_file

        # Parse indyctl.cfg
        self.config = configparser.ConfigParser()
        config_sections = self.config.read(self.indctl_config_file)
        logging.info("Config sections {}".format(config_sections))

        # Error handling ?
        didwallet = IndyctlConfig.__parse_all_yaml(self.resource_dir / "didwallet.yml")
        self.dids = didwallet[0]["dids"]
        self.wallets = didwallet[1]["wallets"]
        logging.info("Dids {}".format(self.dids))
        logging.info("Wallets {}".format(self.wallets))

        schemacred = IndyctlConfig.__parse_all_yaml(self.resource_dir / "schemacred.yml")
        self.schemas = schemacred[0]["schemas"]
        self.creds = schemacred[1]["creds"]
        logging.info("Schemas {}".format(self.schemas))
        logging.info("Creds {}".format(self.creds))

        pool = IndyctlConfig.__parse_all_yaml(self.resource_dir / "pool.yml")
        self.pools = pool[0]["pools"]
        logging.debug("Pools {}".format(self.pools))

        self.created_dir = self.indyctl_dir / "created"
        self.created_schemas_file = self.created_dir / "schemas.json"
        self.created_creds_file = self.created_dir / "creds.json"

    def __parse_all_yaml(path):
        with open(path, "r") as f:
            return list(yaml.safe_load_all(f))