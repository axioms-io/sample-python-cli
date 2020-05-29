import click
import webbrowser
from halo import Halo
import requests
import os
import dotenv
import time
from box import Box
from rich import print
from rich.table import Table, Column

dotenv.load_dotenv('/mnt/g/work/Axioms/sample-python-cli/.env')
C_ID = os.getenv('CLIENT_ID')
TENANT_DOMAIN = os.getenv('TENANT_DOMAIN')
TOKEN_DIR = os.getenv('TOKEN_DIR')

spinner = Halo(text='Loading', spinner='dots')

# Errors/exceptions that are being used for the program
class SampleError(Exception):
    def __init__(self, message):
        self.message = message 

class ExpiredTokenError(SampleError):
    '''Error raised when the expiry of the device code has been exceeded'''

class AccessDeniedError(SampleError):
    '''Error raised when the access has been denied by end user'''

class SlowDownError(SampleError):
    '''Error raised when poll interval needs to be increased by 5 seconds'''

class AuthPendingError(SampleError):
    '''Error raised when poll can continue after interval'''

class FourHundredError(SampleError):
    '''Error in which response from request is 400 or greater'''

@click.group()
def cli():
    pass

@click.command()
def info():
    """Provides some information about the Axioms CLI"""
    click.echo('🚀 Axioms CLI. Manage your Axioms tenant including all '
               'Tenant configurations, OpenID Connect Configurations, Users,'
               'directly from your favourite terminal.')

@click.command()
def login():
    """Asks user to login to Axioms account by opening Axiom login page"""
    # Begins login process
    click.echo('➡️  Starting Authorization')
    
    # Beginning post request to device endpoint to obtain device_code, user_code, etc
    scope = 'openid profile email orgs roles permissions offline_response'
    client_data = {'client_id': C_ID, 'scope': scope}
    url = 'https://{}/oauth2/device'.format(TENANT_DOMAIN)
    check_device_code = 1
    try:
        device_resp = requests.post(url, data=client_data, timeout=15, verify=False)
        device_dict = Box(device_resp.json())
        if device_resp.status_code >= 400:
            raise FourHundredError('Something went wrong.')
    except FourHundredError as e:
        print(f'[bold red]{e.message}[/bold red]')
        check_device_code = 0
    if check_device_code == 0:
        return
    #print(device_dict)
    token_dict = exchange_code_for_token(device_dict)
    
    # Putting the token in seperate dir
    if token_dict != 0:
        token_loc = '{}/tokens'.format(TOKEN_DIR)
        with open(token_loc, 'w') as f:
            f.write(token_dict.access_token)
            f.write('\n')
            f.write(token_dict.token_type)
        #print(token_dict)
    return

def poll(url, req_data, interval, time_out):
    # Polls to tenant domain and requests access_token
    check_access = 1
    while True:
        try:
            token_resp = requests.post(url, data=req_data, verify=False)
            token_dict = Box(token_resp.json())
            if 'error' not in token_dict:
                print(f'[bold blue]Authorization successful!!![/bold blue]')
                break
            if token_dict.error == 'access_denied':
                raise AccessDeniedError("Access has been denied.")
            elif token_dict.error == 'expired_token' or time.time() >= time_out:
                raise ExpiredTokenError('Time has expired, please try again.')
            elif token_dict.error == 'slow_down':
                raise SlowDownError('Increasing interval time by 5 seconds.')
            elif token_dict.error == 'authorization_pending':
                raise AuthPendingError("Continuing polling after interval.")
        except AccessDeniedError as e:
            print(f'[bold red]{e.message}[/bold red]')
            check_access = 0
            break
        except ExpiredTokenError as e:
            print(f'[bold red]{e.message}[/bold red]')
            check_access = 0
            break
        except SlowDownError as e:
            #print(e.message)
            interval += 5
        except AuthPendingError as e:
            #print(e.message)
            pass     
        time.sleep(interval)
    if check_access == 0: 
        return 0
    return token_dict

def  exchange_code_for_token(response):
    # Getting necessary variables 
    device_code = response.device_code
    user_code = response.user_code
    verification_uri = response.verification_uri
    verification_uri_complete = response.verification_uri_complete
    interval = response.interval
    expire = response.expires_in
    
    # Opening the browser (or providing url in the event browser does not open) to verification uri where user enters the user_code
    # use verifciation uri complete for convenience
    click.echo(f'➡️  Please follow the instructions on the following page: {verification_uri_complete}')
    print(f'[bold magenta]If webpage does not open, please input the following code after opening the url provided below:')
    uc_table = Table(show_header=True, header_style='bold blue')
    uc_table.add_column('Code')
    uc_table.add_column('URL')
    uc_table.add_row(f'[bold green]{user_code}[/bold green]', f'[bold blue]{verification_uri}[/bold blue]')
    print(uc_table)
    webbrowser.open_new(verification_uri_complete)  
    
    # Polling device code to token endpoint to get access token
    url = 'https://{}/oauth2/token'.format(TENANT_DOMAIN)
    req_data = {'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
                'device_code': device_code, 
                'client_id': C_ID}
    time_out = time.time() + expire
    time.sleep(interval)
    token_dict = poll(url, req_data, interval, time_out)
    return token_dict

@click.command()
def register():
    """Asks user to register to Axioms by opening Axiom registration page"""
    click.echo('➡️  Opening registration page')
    url = 'https://{}/register'.format(TENANT_DOMAIN)
    webbrowser.open_new(url)
    click.echo('➡️ After registration run ax login or axioms login')

cli.add_command(info)
cli.add_command(login)
cli.add_command(register)
