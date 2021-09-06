import re
import click
from dynaconf import Dynaconf
import os
import sys
from loguru import logger




@click.command()
@click.option("--grid_list",
              default=None,
              help="""Path to a txt file with the tiles you want to process. Example of file content: ['T223071','T001057']. A list of tiles can also be entered in the following format \"T001057, T001002, T223071\"""")
@click.option(
    "--collection",
    default=5,
    help="Choose the sort script for a specific collection. 5 or 6",
)
@click.option("--start_year",  default=None, help="Starting year of classification.")
@click.option("--end_year", default=None, help="Final year of classification.")
@click.option("--force_login", is_flag=True, help="Used to force a login to Google Earth Engine so that you can change the account that will process maps.")
def main(grid_list, collection, start_year, end_year, force_login):

    def start_info(collection, s):
        logger.info(f"You are processing collection number {collection}, for the years {s.START_YEAR} to {s.END_YEAR}, and {len(s.GRIDLIST)} tiles will be processed. Number of random trees is {s.RFNTREES}. Fraction (10 ^ -2%) of the variables in the exchange is set to {s.RFBAGFRACTION}. Variable number per tree branch is {s.RFVARPERSPLIT}")
    config = {
        "settings_file": "settings.toml",  # location of config file
        "environments": ["collection5", "collection6"],
    }
    if not start_year == None:
        os.environ["DYNACONF_START_YEAR"] = start_year
    if not end_year == None:
        os.environ["DYNACONF_END_YEAR"] = end_year

    if not grid_list == None:
        pat = re.compile(r"^(T\d{6},|T\d{6}, {1,4})+T\d{6}|^T\d{6}")
        fall = f'Unable to load tile list\nPlease display the file exists, or if a list in the given terminal is valid'
        try:
            with open(grid_list) as f:
                read_data = f.read()
            os.environ["DYNACONF_GRIDLIST"] = read_data
        except FileNotFoundError as e:
            try:
                if re.fullmatch(pat, grid_list.upper()):
                    normalise = grid_list.replace(' ', '').upper().split(',')
                    os.environ["DYNACONF_GRIDLIST"] = str(normalise)
                else:
                    logger.warning(fall)
                    sys.exit(1)
            except Exception as e2:
                logger.warning(fall)
                sys.exit(1)

    if force_login:
        import ee
        ee.Authenticate()
        ee.Initialize()
    if collection == 5:
        settings = Dynaconf(**config, env="COLLECTION5")
        from Pasture.classification.mapbiomas50 import main as main50
        start_info(collection, settings)
        main50(settings)
    else:
        settings = Dynaconf(
            **config,
            env="COLLECTION6",
        )
        from Pasture.classification.mapbiomas60 import main as main60
        start_info(collection, settings)
        main60(settings)


if __name__ == "__main__":
    main()
