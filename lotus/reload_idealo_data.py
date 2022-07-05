from lotus import *

client_id = '54743bc2-5f71-4143-a52a-a9502dcf4587'
client_pw = 'D2;jS$lnL0Z5,'
header = {'Content-Type': 'application/x-www-form-urlencoded'}
auth = requests.post('https://api.idealo.com/mer/businessaccount/api/v1/oauth/token', headers=header,
                     auth=HTTPBasicAuth(client_id, client_pw), data={'grant_type': 'client_credentials'})

json_data = auth.json()

header = {"Authorization": "Bearer " + json_data['access_token'], 'Accept': 'application/json',
          'Content-Type': 'application/json; charset=UTF-8', 'scope': json_data['scope']}

ps = Product.query.order_by(Product.id).all()

for p in ps:
    print(p.id)
    marketplace = Marketplace.query.filter_by(name='Idealo').first()
    mpa = Marketplace_Product_Attributes.query.filter_by(product_id=p.id, marketplace_id=marketplace.id).first()

    if mpa.selling_price == None:
        mpa.selling_price=0
        db.session.commit()
    sku = p.internal_id
    shop_id = '318578'

    url = "https://import.idealo.com/shop/" + shop_id + "/offer/" + sku + "/"
    requests.delete(url=url, headers=header)

    patch_dict = {'title': mpa.name,
                  'url': 'https://www.ebay.de/usr/lotusicafe',
                  'brand': p.brand,
                  'description': mpa.get_descriptions(),
                  'imageUrls': p.picturearray(),
                  'packagingUnit': 1,
                  'eans': [mpa.search_term],
                  'hans': [p.mpn],
                  'merchantName': 'lotusicafe',
                  'merchantId': shop_id,
                  'checkout': True,
                  'quantityPerOrder': 5,
                  'fulfillmentType': 'PARCEL_SERVICE',
                  'sku': sku,
                  'price': ("%.2f" % mpa.selling_price),
                  'checkoutLimitPerPeriod': int(p.get_own_stock()),
                  'delivery': mpa.shipping_dhl_time,
                  'deliveryComment': mpa.shipping_dhl_comment
                  }

    deliverydict = {}
    if mpa.shipping_dhl_cost is not None:
        deliverydict['DHL'] = ("%.2f" % mpa.shipping_dhl_cost)
    if mpa.shipping_dp_cost is not None:
        deliverydict['DEUTSCHE_POST'] = ("%.2f" % mpa.shipping_dp_cost)
    if mpa.shipping_dpd_cost is not None:
        deliverydict['DPD'] = ("%.2f" % mpa.shipping_dpd_cost)
    if mpa.shipping_hermes_cost is not None:
        deliverydict['HERMES'] = ("%.2f" % mpa.shipping_hermes_cost)

    put_dict = {'sku': sku,
                'title': mpa.name,
                'price': ("%.2f" % mpa.selling_price),
                'url': 'https://www.ebay.de/usr/lotusicafe',
                'brand': p.brand,
                'description': mpa.get_descriptions(),
                'imageUrls': p.picturearray(),
                'packagingUnit': 1,
                'eans': [mpa.search_term],
                'hans': [p.mpn],
                'merchantName': 'lotusicafe',
                'merchantId': shop_id,
                'paymentCosts': {'PAYPAL': "0.00"},
                'deliveryCosts': deliverydict,
                'delivery': mpa.shipping_dhl_time,
                'deliveryComment': mpa.shipping_dhl_comment,
                'checkout': True,
                'checkoutLimitPerPeriod': int(p.get_own_stock()),
                'quantityPerOrder': 0,
                'fulfillmentType': 'PARCEL_SERVICE',
                }

    URL = "https://import.idealo.com/shop/" + shop_id + "/offer/" + sku + "/"

    requests.put(url=URL, json=put_dict, headers=header)
    requests.patch(url=URL, json=patch_dict, headers=header)

    response = p.generate_idealo_price()

    print(response)
    print('-----------------')