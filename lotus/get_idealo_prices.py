# -*- coding: utf-8 -*-

from lotus import *
from requests.auth import HTTPBasicAuth
import zipfile
import re
from io import TextIOWrapper, BytesIO
import time as t


shop_id = '318578'
client_id = '5a07691f-53b0-4e09-8268-e7a115a7dd12'
client_pw = 'G%!s/mv9LdZS9&1'
header = {'Content-Type': 'application/x-www-form-urlencoded'}
auth = requests.post('https://api.idealo.com/mer/businessaccount/api/v1/oauth/token', headers=header,  auth=HTTPBasicAuth(client_id, client_pw), data={'grant_type': 'client_credentials'})
json_data = auth.json()
idealo = Marketplace.query.filter_by(name='Idealo').first()

header = {"Authorization": "Bearer " + json_data['access_token'], 'Accept': 'application/json',
          'Content-Type': 'application/json; charset=UTF-8', 'scope': json_data['scope']}
s = requests.post(url=f"https://businessapi.idealo.com/api/v1/shops/{shop_id}/price-reports", headers=header, json={"site": "IDEALO_DE"})
report_id = s.json()['id']

status = 'PROCESSING'
while status == 'PROCESSING':
    print('PROCESSING')
    print('Wait 60 seconds.')
    print('---------------------------')
    s = requests.get(url=f'https://businessapi.idealo.com/api/v1/shops/{shop_id}/price-reports/{report_id}', headers=header)
    status = s.json()['status']
    t.sleep(60)

if status == 'SUCCESSFUL':
    print('SUCCESSFUL!')
    print('---------------------------')
    update = datetime.now().replace(microsecond=0, second=0, minute=0)
    marketplace = Marketplace.query.filter_by(name='Idealo').first()

    licSeller = ExtSeller.query.filter_by(name='lotusicafe').first()
    licPlatform = ExtPlatform.query.filter_by(name='lotusicafe').first()
    extSeller = ExtSeller.query.filter_by(name='Unbekannt').first()
    extPlatform = ExtPlatform.query.filter_by(name='Unbekannt').first()

    offerDict = {}
    # offerDict = {idealoID: {SKUs: [SKU1, SKU2, ...}, offers: [[SellerID, PlatformID, sellingPrice, shippingPrice, delivery_time], [SellerID, PlatformID, sellingPrice, shippingPrice, delivery_time], ...]}
    rankDict = {}

    s = requests.get(url=f'https://businessapi.idealo.com/api/v1/shops/{shop_id}/price-reports/{report_id}/download', headers=header)
    with zipfile.ZipFile(BytesIO(s.content)) as z:
        for filename in z.namelist():
            with z.open(filename, 'r') as csv_file:
                csv_reader = csv.reader(TextIOWrapper(csv_file, 'utf-8'))
                i = 0
                for row in csv_reader:
                    print(i)
                    if i <= 1:
                        i += 1
                        continue
                    idealoID = row[1].split('/')[-1]
                    own_pos = int(re.sub('[^0-9]', '', row[5]))
                    sku = row[3]
                    rankDict[sku] = own_pos
                    if idealoID in offerDict:
                        print(idealoID)
                        print(row[3])
                        try:
                            if len(offerDict[idealoID]['offers']) > own_pos - 1:
                                offerDict[idealoID]['offers'][own_pos - 1][0] = licSeller.id
                                offerDict[idealoID]['offers'][own_pos - 1][1] = licPlatform.id
                            offerDict[idealoID]['SKUs'].append(sku)
                        except Exception as e:
                            print(e)
                            offerDict[idealoID]['SKUs'].append(sku)
                    else:
                        for k in range(10):
                            try:
                                if k == int(re.sub('[^0-9]', '', row[5])) - 1:
                                    seller_id = licSeller.id
                                    platform_id = licPlatform.id
                                else:
                                    seller_id = extSeller.id
                                    platform_id = extPlatform.id
                            except Exception as e:
                                print(e)
                                seller_id = extSeller.id
                                platform_id = extPlatform.id
                            price_w_sh = str_to_float(money_to_float(row[12 + k * 4]))
                            if price_w_sh == None:
                                continue
                            selling_price = str_to_float(money_to_float(row[10 + k * 4]))
                            shipping_price = str_to_float(money_to_float(row[11 + k * 4]))
                            if shipping_price == None:
                                shipping_price = 0
                            delivery_time = row[13 + k * 4]
                            if k == 0:
                                offerDict[idealoID] = {'SKUs': [sku], 'offers': [[seller_id, platform_id, selling_price, shipping_price, delivery_time]]}
                            else:
                                offerDict[idealoID]['offers'].append([seller_id, platform_id, selling_price, shipping_price, delivery_time])
                    i += 1
                print(offerDict)
                i = 0
                for key in offerDict:
                    skus = offerDict[key]['SKUs']
                    print('------------------')
                    print(i)
                    print(skus)
                    query = db.session.query(
                        Product, Marketplace_Product_Attributes
                    ).filter(
                        Product.id == Marketplace_Product_Attributes.product_id
                    ).filter(
                        idealo.id == Marketplace_Product_Attributes.marketplace_id
                    ).filter(
                        Product.internal_id.in_(skus)
                    ).all()
                    k = 0
                    for offer in offerDict[key]['offers']:
                        seller_id = offer[0]
                        platform_id = offer[1]
                        selling_price = offer[2]
                        shipping_price = offer[3]
                        delivery_time = offer[4]
                        for product, mpa in query:
                            checklink = ProductLink.query.filter_by(product_id=product.id, category_id=4).first()
                            if checklink:
                                if checklink.link:
                                    if 'Offers' not in checklink.link:
                                        checklink.link = f'https://www.idealo.de/preisvergleich/OffersOfProduct/{key}'
                                        db.session.commit()
                                else:
                                    checklink.link = f'https://www.idealo.de/preisvergleich/OffersOfProduct/{key}'
                                    db.session.commit()
                            else:
                                db.session.add(ProductLink(f'https://www.idealo.de/preisvergleich/OffersOfProduct/{key}', 4, product.id))
                                db.session.commit()
                            db_offer = ExtOffer.query.order_by(ExtOffer.init_date.desc()).filter_by(seller_id=offer[0], platform_id=offer[1], product_id=product.id, marketplace_id=marketplace.id,
                                                                                                    selling_price=offer[2], shipping_price=offer[3]).first()
                            if db_offer is None:
                                db_offer = ExtOffer(offer[2], offer[3], None, k + 1, offer[4], None, None, None, marketplace.id, offer[1], product.id, offer[0])
                                db.session.add(db_offer)
                            else:
                                if (offer[2] != db_offer.selling_price
                                        or offer[3] != db_offer.shipping_price
                                        or offer[4] != db_offer.delivery_time):
                                    db_offer = ExtOffer(offer[2], offer[3], None, k + 1, offer[4], None, None, None, marketplace.id, offer[1], product.id, offer[0])
                                    db.session.add(db_offer)
                                else:
                                    db_offer.last_seen = update
                            mpa.curr_rank = rankDict[product.internal_id] if product.internal_id in rankDict else None
                            db.session.commit()
                        k += 1
                    i += 1

else:
    print('FAILED!')
    print(s.text)

