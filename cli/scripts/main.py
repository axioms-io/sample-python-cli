import click
import webbrowser
from halo import Halo

spinner = Halo(text='Loading', spinner='dots')

@click.group()
def cli():
    pass

@click.command()
def info():
    click.echo('🚀 Axioms CLI. Manage your Axioms tenant including all '
               'Tenant configurations, OpenID Connect Configurations, Users,'
               'directly from your favourite terminal.')

@click.command()
def login():
    click.echo('➡️  Starting Authorization')
    url = 'https://axioms.us.axioms.io/user/login'
    webbrowser.open_new(url)
    auth_code = get_auth_code()

def get_auth_code():
    auth_code = input('➡️  Please enter authorization code on your screen: ').strip()
    return auth_code

def  exchange_code_for_token():
    pass

def refresh 

@click.command()
def register():
    click.echo('➡️  Opening registration page')
    url = 'https://axioms.us.axioms.io/user/register'
    webbrowser.open_new(url)
    click.echo('➡️ After registration run ax login or axioms login')

cli.add_command(info)
cli.add_command(login)
cli.add_command(register)