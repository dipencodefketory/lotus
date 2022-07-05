# -*- coding: utf-8 -*-

import entertainment_trading as et


orders = et.get_orders().json()

for o in orders['results']:
    print(o)