from ServeStatus.app import create_app
from Lapig.Functions import __login_manual
import ee
import click

@click.command()
@click.option('--login', 
    default = False,
    help = 'Força login no GEE' )
def start(login):
    if login == True:
        __login_manual(ee)
    else:
        login_gee(ee)
    create_app()