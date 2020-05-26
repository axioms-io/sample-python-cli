import click
import webbrowser
from halo import Halo
import requests
import os
import dotenv
import polling
import time

dotenv.load_dotenv('/mnt/g/work/Axioms/sample-python-cli/.env')
C_ID = os.getenv('CLIENT_ID')
TENANT_DOMAIN = os.getenv('TENANT_DOMAIN')

spinner = Halo(text='Loading', spinner='dots')

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
    # url = 'https://axioms.us.axioms.io/user/login'
    # url = 'https://test-unlimited.uat.us.axioms.io/user/register' <------ TRY THISSSS
    # the other one is not working apparently
    # url = TENANT_DOMAIN + 'user/login'
    # login_url = 'https://axioms.us.uat.axioms.io/user/login'
    # webbrowser.open_new(login_url)
    
    # Beginning post request to device endpoint to obtain device_code, user_code, etc
    scope = 'openid profile email orgs roles permissions offline_response'
    client_data = {'client_id': C_ID, 'scope': scope}
    url = "https://{}/oauth2/device".format(TENANT_DOMAIN)
    print(url)
    device_resp = requests.post(url, data=client_data, timeout=15, verify=False)
    print(device_resp.json())
    exchange_code_for_token(device_resp)
    # add try except to handle error

# def get_auth_code():
#     auth_code = input('➡️  Please enter authorization code on your screen: ').strip()
#     return auth_code

def  exchange_code_for_token(response):
    # Getting necessary variables 
    # use python box package
    resp_dict = response.json()
    device_code = resp_dict['device_code']
    user_code = resp_dict['user_code']
    verification_uri = resp_dict['verification_uri']
    verification_uri_complete = resp_dict['verification_uri_complete']
    interval = resp_dict['interval']
    expire = resp_dict['expires_in']
    
    # Opening the browser (or providing url in the event browser does not open) to verification uri where user enters the user_code
    # use verifciation uri complete for convenience
    click.echo('➡️  Please enter the given user code when prompted on website. If no webpage has been opened, please go to following link: {verification_uri}')
    click.echo(f'User code: {user_code}')
    
    # Polling device code to token endpoint to get access token
    url = "https://{}/oauth2/token".format(TENANT_DOMAIN)
    req_data = {'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
                'device_code': device_code, 
                'client_id': C_ID}
    webbrowser.open_new(verification_uri_complete)   
    time.sleep(interval)
    try:
        token_response = polling.poll(lambda: requests.post(url, data=req_data),    
                                    timeout=expire, 
                                    step=interval,verify=False)
    except polling.TimeoutException:
        click.echo('Time out error. Please try again.') 
    print(token_response.json())

#def refresh 

@click.command()
def register():
    """Asks user to register to Axioms by opening Axiom registration page"""
    click.echo('➡️  Opening registration page')
    #url = 'https://axioms.us.axioms.io/user/register'
    #url = 'https://test-unlimited.uat.us.axioms.io/user/register' <------ TRY THISSSS
    url = 'https://axioms.us.uat.axioms.io/user/register'
    webbrowser.open_new(url)
    click.echo('➡️ After registration run ax login or axioms login')

cli.add_command(info)
cli.add_command(login)
cli.add_command(register)

if __name__ == '__main__':
    cli()

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