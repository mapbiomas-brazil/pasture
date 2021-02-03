import click
from ClineteGEE.cliente import main 
@click.command()
def start():
    main()



if __name__ == '__main__':
    start()
    