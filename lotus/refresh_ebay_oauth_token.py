# -*- coding: utf-8 -*-

"""EBAY API-CALLS"""

from lotus import env_vars_path
from dotenv import load_dotenv, set_key
import ebay_api
import os

load_dotenv(env_vars_path)

r = ebay_api.refresh_access_token(os.environ['EBAY_OAUTH_REFRESH_TOKEN'])
data = r.json()
print(data)
set_key(env_vars_path, 'EBAY_OAUTH_TOKEN', data['access_token'])
load_dotenv('/home/lotus2/webapp/.env')
set_key('/home/lotus2/webapp/.env', 'EBAY_OAUTH_TOKEN', data['access_token'])

