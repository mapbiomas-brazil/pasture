import click
from dynaconf import Dynaconf
import os
import sys



# rfNTrees = 200 # Number of random trees;
# rfBagFraction = 0.5 # Fraction (10^-2%) of variables in the bag;
# rfVarPersplit = 6  # Number of varibales per tree branch;


@click.command()
@click.option("--grid_list", default=None, help="")
@click.option(
    "--collection",
    default=5,
    help="Choose the sort script for a specific collection. 5 or 6",
)
@click.option("--start_year", default=None, help="Starting year of classification.")
@click.option("--end_year", default=None, help="Final year of classification.")
@click.option("--force_login", default=None, help="Final year of classification.")
def main(grid_list, collection, start_year, end_year, force_login):
    config = {
        "settings_file": "settings.toml",  # location of config file
        "environments": ["collection5", "collection6"],
    }
    if not start_year == None:
        os.environ["DYNACONF_START_YEAR"] = start_year
    if not end_year == None:
        os.environ["DYNACONF_END_YEAR"] = end_year

    if not grid_list == None:
        try:
            with open(grid_list) as f:
                read_data = f.read()
            os.environ["DYNACONF_GRIDLIST"] = read_data
        except Exception as e:
            print(f"{e}")
            sys.exit(1)

    if not force_login == None:
        import ee

        ee.Authenticate()
        ee.Initialize()
    if collection == 5:
        settings = Dynaconf(**config, env="COLLECTION5")
        from Pasture.classification.mapbiomas50 import main as main50

        main50(settings)
    else:
        settings = Dynaconf(
            **config,
            env="COLLECTION6",
        )
        from Pasture.classification.mapbiomas60 import main as main60

        main60(settings)


if __name__ == "__main__":
    main()
