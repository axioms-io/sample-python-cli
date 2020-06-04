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
# from click_configfile import ConfigFileReader, Param, SectionSchema, matches_section

# class ConfigFileLayout(object):
#     @matches_section('client_id'):
#     class Client_id(SectionSchema):
#         C_ID = Param(type=str)
#         TENANT_DOMAIN = Param(type=str) 
        
#     @matches_section('user')
#     class Access_token(SectionSchema):
#         header = Param(type=str)
#         token = Param(type=str)
    
# class ConfigFileFinder(ConfigFileReader):
#     cfg_files = ['token.cfg']
#     cfg_schema = [
#         ConfigFileLayout.Client_id,
#         ConfigFileLayout.Access_token
#     ]

# CONTEXT_SETTINGS = dict(default_map=ConfigFileFinder.read_config())

dotenv.load_dotenv('/mnt/g/work/Axioms/sample-python-cli/.env')
C_ID = os.getenv('CLIENT_ID')
TENANT_DOMAIN = os.getenv('TENANT_DOMAIN')
TOKEN_DIR = os.getenv('TOKEN_DIR')
RESOURCE_URL = 'https://shafi-sample-flask-app.herokuapp.com/'

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

@click.command() # add this when using click config: context_settings=CONTEXT_SETTINGS
#@click.pass_context 
def login(): #add the parameter ctx here when using click config
    """Asks user to login to Axioms account by opening Axiom login page"""
    # Begins login process
    click.echo('➡️  Starting Authorization')
    # for data in context.default_map.keys():
    #     if data.starts_with('client_id'):
    #         client_info = context.default_map[data]
    # c_id = client_info['client_id']
    # token_domain = client_info['token_domain']
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
            f.write(token_dict.access_token.rstrip('\r\n'))
            # f.write('\n')
            # f.write(token_dict.token_type)
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

@click.command()
@click.argument('req', default='get')
def public(req):
    """Resource from public endpoint, can only use get request"""
    if req == 'get':
        resp = requests.get('{}/public'.format(RESOURCE_URL), timeout=10)
        resp_dict = Box(resp.json())
        print(f'[bold blue]{resp_dict.message}[/bold blue]')
    else:
        print(f'[bold magenta]Invalid request to this endpoint.[/bold magenta]')
    return

@click.command()
@click.argument('req', default='get')
def private(req):
    """Resource from private endpoint, can only use get request"""
    token_loc = '{}/tokens'.format(TOKEN_DIR)
    with open(token_loc, 'r') as f:
        access_token = f.read().replace('\n', '')
    if req == 'get':
        resp = requests.get('{}/private'.format(RESOURCE_URL), headers={'Authorization': 'Bearer {}'.format(access_token)}, timeout=10)
        resp_dict = Box(resp.json())
        if 'message' in resp_dict: 
            print(f'[bold blue]{resp_dict.message}[/bold blue]')
        else:
            print(f'[bold magenta]{resp_dict}[/bold magenta]')
    else:
        print(f'[bold magenta]Invalid request to this endpoint.[/bold magenta]')
    return

@click.command()
@click.argument('req', default='get')
def permission(req):
    """Resource from permission endpoint, can use get, post, patch and delete requests"""
    token_loc = '{}/tokens'.format(TOKEN_DIR)
    with open(token_loc, 'r') as f:
        access_token = f.readline()
    req_data = {'Authorization': 'Bearer {}'.format(access_token.strip('\n'))}
    if req == 'get':
        resp = requests.get('{}/permission'.format(RESOURCE_URL), headers=req_data, timeout=10)
    elif req == 'post':
        resp = requests.post('{}/permission'.format(RESOURCE_URL), headers=req_data, timeout=10)
    elif req == 'patch':
        resp = requests.patch('{}/permission'.format(RESOURCE_URL), headers=req_data, timeout=10)
    elif req == 'delete':
        resp = requests.delete('{}/permission'.format(RESOURCE_URL), headers=req_data, timeout=10)
    else:
        print(f'[bold magenta]Invalid request to this endpoint.[/bold magenta]')
    resp_dict = Box(resp.json())
    if 'message' in resp_dict: 
        print(f'[bold blue]{resp_dict.message}[/bold blue]')
    else:
        print(f'[bold magenta]{resp_dict}[/bold magenta]')
    return

@click.command()
@click.argument('req', default='get')
def role(req):
    """Resource from role endpoint, can use get, post, patch and delete requests"""
    token_loc = '{}/tokens'.format(TOKEN_DIR)
    with open(token_loc, 'r') as f:
        access_token = f.readline()
    req_data = {'Authorization': 'Bearer {}'.format(access_token.strip('\n'))}
    if req == 'get':
        resp = requests.get('{}/role'.format(RESOURCE_URL), headers=req_data, timeout=10)
    elif req == 'post':
        resp = requests.post('{}/role'.format(RESOURCE_URL), headers=req_data, timeout=10)
    elif req == 'patch':
        resp = requests.patch('{}/role'.format(RESOURCE_URL), headers=req_data, timeout=10)
    elif req == 'delete':
        resp = requests.delete('{}/role'.format(RESOURCE_URL), headers=req_data, timeout=10)
    else:
        print(f'[bold magenta]Invalid request to this endpoint.[/bold magenta]')
    resp_dict = Box(resp.json())
    if 'message' in resp_dict: 
        print(f'[bold blue]{resp_dict.message}[/bold blue]')
    else:
        print(f'[bold magenta]{resp_dict}[/bold magenta]')
    return

cli.add_command(info)
cli.add_command(login)
cli.add_command(register)
cli.add_command(public)
cli.add_command(private)
cli.add_command(permission)
cli.add_command(role)
