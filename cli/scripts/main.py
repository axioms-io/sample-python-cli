import click
import webbrowser
from halo import Halo
import requests
import os
import dotenv
import time
from box import Box
from rich import print

dotenv.load_dotenv('/mnt/g/work/Axioms/sample-python-cli/.env')
C_ID = os.getenv('CLIENT_ID')
TENANT_DOMAIN = os.getenv('TENANT_DOMAIN')

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
    device_resp = requests.post(url, data=client_data, timeout=15, verify=False)
    device_dict = Box(device_resp.json())
    #print(device_dict)
    exchange_code_for_token(device_dict)
    # add try except to handle error

def poll(url, req_data, interval, time_out):
    # Polls to tenant domain
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
            print(f'[bold magenta]{e.message}[/bold magenta]')
            break
        except ExpiredTokenError as e:
            print(f'[bold magenta]{e.message}[/bold magenta]')
            break
        except SlowDownError as e:
            #print(e.message)
            interval += 5
        except AuthPendingError as e:
            #print(e.message)
            pass     
        time.sleep(interval)
    return token_dict

def  exchange_code_for_token(response):
    # Getting necessary variables 
    # use python box package
    # resp_dict = response.json()
    device_code = response.device_code
    user_code = response.user_code
    verification_uri = response.verification_uri
    verification_uri_complete = response.verification_uri_complete
    interval = response.interval
    expire = response.expires_in
    
    # Opening the browser (or providing url in the event browser does not open) to verification uri where user enters the user_code
    # use verifciation uri complete for convenience
    click.echo(f'➡️  Please follow the instructions on the following page: {verification_uri_complete}')
    webbrowser.open_new(verification_uri_complete)  
    # Polling device code to token endpoint to get access token
    url = 'https://{}/oauth2/token'.format(TENANT_DOMAIN)
    req_data = {'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
                'device_code': device_code, 
                'client_id': C_ID}
    time_out = time.time() + expire
    time.sleep(interval)
    token_dict = poll(url, req_data, interval, time_out)
    print(f'Program fini\n{token_dict}')

#def refresh 

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

# if __name__ == '__main__':
#     cli()

#######################################################################################
# This should happen before client prompts user to login, check auth endpoint in devhub
# after user has logged in, they will get sent to a callback url, at 
# which point this POST requests using client_id and scope to get device code
# to the device endpoint
# use a timeout parameter in request
# device_resp should have device code, user code, verification, etc
# this should then show the user the user code and verification uri, which the
# the user should go to to enter the code. during this, this should poll token 
# endpoint {tnant domain}/oauth2/token with device code
# device_data = {grant_type: , device_code: , client_id: }
# token_resp = request.post('{tenant domain}/oauth2/token', data=device_data)
# response from this will vary, check docs
# try:
    #     token_response = polling.poll(lambda: requests.post(url, data=req_data, verify=False),    
    #                                 timeout=expire, 
    #                                 step=interval)
    # except polling.TimeoutException:
    #     click.echo('Time out error. Please try again.') 