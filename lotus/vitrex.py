# -*- coding: utf-8 -*-

from lotus import *
import ftplib
import math


client_id = '54743bc2-5f71-4143-a52a-a9502dcf4587'
client_pw = 'D2;jS$lnL0Z5,'
header = {'Content-Type': 'application/x-www-form-urlencoded'}
auth = requests.post('https://api.idealo.com/mer/businessaccount/api/v1/oauth/token/', headers=header,
                     auth=HTTPBasicAuth(client_id, client_pw), data={'grant_type': 'client_credentials'})

json_data = auth.json()

req_response = ''
error_message = 'Beim Upload der folgenden Produkte sind Fehler entstanden:\n'
error = False

success_message = 'Die Produkte mit den IDs '

filename = 'Vitrex_Artikelstamm_Bilder.csv'

ftp = ftplib.FTP("80.147.95.142")
ftp.login("40790", "vtyh3VJD")
ftp.retrbinary("RETR " + filename, open(filename, 'wb').write)
ftp.quit()

counter = 0

order = Order(datetime.now())
order.supplier_id = 4
order.payment_method_id = 5
order.label = 'Vitrex Upload'
order.comment = ''
order.additional_cost = 0
order.delivery_time = datetime.now()
order.price = 0
db.session.add(order)
db.session.commit()
with open('Vitrex_Artikelstamm_Bilder.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=';')
    i=0
    for row in csv_reader:
        print(i)
        if i==0:
            i+=1
            continue
        if row[10]=='' or row[4] in ['BuchHeft', 'Code-Card', 'Guthaben Karte Online', 'Merchandise', 'Spielzeug'] or row[7]==0:
            counter +=1
            print('continued')
            continue
        prod_ean = row[10].replace('          ',' - ').replace('         ',' - ').replace('        ',' - ').replace('       ',' - ').replace('      ',' - ').replace('     ',' - ').replace('    ',' - ').replace('   ',' - ').replace('  ',' - ')
        prod_name = row[1].replace('          ',' - ').replace('         ',' - ').replace('        ',' - ').replace('       ',' - ').replace('      ',' - ').replace('     ',' - ').replace('    ',' - ').replace('   ',' - ').replace('  ',' - ')
        if row[3] != '':
            prod_name += ' - ' + row[3]

        if len(prod_name)>80:
            prod_name = prod_name[:80].rsplit(' ',1)[0]
        prod_brand = row[5].replace('          ',' - ').replace('         ',' - ').replace('        ',' - ').replace('       ',' - ').replace('      ',' - ').replace('     ',' - ').replace('    ',' - ').replace('   ',' - ').replace('  ',' - ')

        prod_quant = 0
        prod_tax = 19
        prod_price = float(row[11].replace(',','.'))

        stock = int(row[7])
        dscrpt = row[19]

        while len(prod_ean) < 13:
            prod_ean = '0' + prod_ean
        product = Product.query.filter_by(HSP_ID=prod_ean).first()
        if not product:
            product = Product('EAN', prod_ean)
            product.name = prod_name
            db.session.add(product)

            bigpicture = ProductPicture(0, re.sub("[^a-zA-Z0-9]+", "", deumlaut(prod_name)) + '1.jpg')
            db.session.add(bigpicture)
            product.pictures.append(bigpicture)

            smallpicture = ProductPicture(1, re.sub("[^a-zA-Z0-9]+", "", deumlaut(prod_name)) + '2.jpg')
            db.session.add(smallpicture)
            product.pictures.append(smallpicture)

            addpicture = ProductPicture(2, re.sub("[^a-zA-Z0-9]+", "", deumlaut(prod_name)) + '3.jpg')
            db.session.add(addpicture)
            product.pictures.append(addpicture)

            article = Article(product.id)
            article.dscrpt_0 = dscrpt
            article.brand = prod_brand
            article.buying_price = prod_price
            article.quantity = 0
            db.session.add(article)

            product.article = article

            newebayattr = Ebay_Article_Attributes(article.id)
            db.session.add(newebayattr)

            newidealoattr = Idealo_Article_Attributes(article.id)
            newidealoattr.uploaded = False
            db.session.add(newidealoattr)

            article.ebay_attributes = newebayattr
            article.idealo_attributes = newidealoattr

            db.session.commit()

        if product.Internal_ID == None or product.Internal_ID == '':
            url = "https://api.afterbuy.de/afterbuy/ABInterface.aspx"

            xml = '''<?xml version="1.0" encoding="utf-8"?>
            <Request>
            <AfterbuyGlobal>
            <PartnerID><![CDATA[1000007048]]></PartnerID>
            <PartnerPassword><![CDATA[epK7Ob9QO1geo44zUHqrgPhnU]]></PartnerPassword>
            <UserID><![CDATA[Lotusicafe]]></UserID>
            <UserPassword><![CDATA[210676After251174]]></UserPassword>
            <CallName>GetStockInfo</CallName>
            <DetailLevel>14</DetailLevel>
            <ErrorLanguage>DE</ErrorLanguage>
            </AfterbuyGlobal>
            <Products>
            <Product>
            <Anr>''' + prod_ean + '''</Anr>
            </Product>
            </Products>
            </Request>
            '''
            headers = {'Content-Type': 'application/xml'}
            r = requests.get(url, data=xml, headers=headers)

            tree = ET.fromstring(r.text)
            ID = min([int(item.text) for item in tree.iter() if item.tag == 'ProductID'])

            if ID == 0:
                print(prod_ean)
                print(prod_name)
                anr = prod_ean
                while anr[0] == '0':
                    anr = anr[1:]
                xml = '''<?xml version="1.0" encoding="utf-8"?>
                            <Request>
                                <AfterbuyGlobal>
                                    <PartnerID><![CDATA[1000007048]]></PartnerID>
                                    <PartnerPassword><![CDATA[epK7Ob9QO1geo44zUHqrgPhnU]]></PartnerPassword>
                                    <UserID><![CDATA[Lotusicafe]]></UserID>
                                    <UserPassword><![CDATA[210676After251174]]></UserPassword>
                                    <CallName>UpdateShopProducts</CallName>
                                    <DetailLevel>0</DetailLevel>
                                    <ErrorLanguage>DE</ErrorLanguage>
                                </AfterbuyGlobal>
                                <Products>
                                    <Product>
                                        <ProductIdent>
                                            <ProductInsert>1</ProductInsert>
                                            <ProductID>0</ProductID>
                                            <Anr>''' + anr + '''</Anr>
                                            <EAN>''' + prod_ean + '''</EAN>
                                        </ProductIdent>
                                        <EAN>''' + prod_ean + '''</EAN>
                                        <Name><![CDATA[''' + prod_name + ''']]></Name>
                                        <Anr>''' + anr + '''</Anr>
                                    </Product>
                                </Products>
                            </Request>
                            '''

                headers = {'Content-Type': 'application/xml'}
                r = requests.get(url, data=xml, headers=headers)

                tree = ET.fromstring(r.text)
                ID = [item.text for item in tree.iter() if item.tag == 'ProductID'][0]
                product.Internal_ID = str(ID)
            else:
                testproduct = Product.query.filter_by(Internal_ID=str(ID)).first()
                if not testproduct:
                    product.Internal_ID = str(ID)
                else:
                    for picture in product.pictures:
                        db.session.delete(picture)
                    if product.article:
                        db.session.delete(product.article.ebay_attributes)
                        db.session.delete(product.article.idealo_attributes)
                        db.session.delete(product.article)
                    db.session.delete(product)
                    db.session.commit()
                    testproduct.HSP_ID_Type = 'EAN'
                    testproduct.HSP_ID = prod_ean
                    product = testproduct
                    db.session.commit()

        new_connection = Order_Article(order.id, product.article.id, prod_quant, prod_price, prod_tax)
        db.session.add(new_connection)
        checkoffer = Supplier_Offer.query.order_by(Supplier_Offer.id.desc()).filter_by(product_id=product.id, supplier_id=3).first()
        if checkoffer:
            if checkoffer.price != prod_price or checkoffer.quantity != stock:
                db.session.add(Supplier_Offer(3,product.id,stock,prod_price))
            else:
                checkoffer.last_seen = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            db.session.add(Supplier_Offer(3, product.id, stock, prod_price))
        db.session.commit()

        if product.article.idealo_attributes.uploaded == False:
            print('---------------------')
            print('Idealo')
            try:

                deliverydict = {}
                deliverydict['DHL'] = '2.99'

                sku = product.Internal_ID

                price = -1.384205 * (2.5126 - prod_price - min(0.06 * prod_price, 12) - 3.953)
                price = math.floor(price)+0.9
                print(prod_name)
                print(price)

                shop_id = '318578'
                put_dict = {'sku': sku,
                            'title': product.name,
                            'price': ("%.2f" % price),
                            'url': 'https://www.ebay.de/usr/lotusicafe',
                            'packagingUnit': 1,
                            'eans': [product.HSP_ID],
                            'merchantName': 'lotusicafe',
                            'merchantId': shop_id,
                            'paymentCosts': {'PAYPAL': "0.00"},
                            'deliveryCosts': deliverydict,
                            'delivery': '2-4 Werktage',
                            'deliveryComment': 'Auf Lager, versandfertig in 48 Stunden.',
                            'checkout': True,
                            'checkoutLimitPerPeriod': 0,
                            'quantityPerOrder': 5,
                            'fulfillmentType': 'PARCEL_SERVICE',
                            }
                patch_dict = {'sku': sku,
                            'title': product.name,
                            'price': ("%.2f" % price),
                            'url': 'https://www.ebay.de/usr/lotusicafe',
                            'packagingUnit': 1,
                            'eans': [product.HSP_ID],
                            'merchantName': 'lotusicafe',
                            'merchantId': shop_id,
                            'delivery': '2-4 Werktage',
                            'deliveryComment': 'Auf Lager, versandfertig in 48 Stunden.',
                            'checkout': True,
                            'checkoutLimitPerPeriod': 0,
                            'quantityPerOrder': 5,
                            'fulfillmentType': 'PARCEL_SERVICE',
                            }
                URL = "https://import.idealo.com/shop/" + shop_id + "/offer/" + sku + "/"
                header = {"Authorization": "Bearer " + json_data['access_token'], 'Accept': 'application/json',
                          'Content-Type': 'application/json; charset=UTF-8', 'scope': json_data['scope']}
                r = requests.put(url=URL, json=put_dict, headers=header)
                s = requests.patch(url=URL, json=put_dict, headers=header)
                req_response += r.text + '\n'

                product.article.idealo_attributes.uploaded = True
                product.article.idealo_attributes.upload_date = datetime.now()

                db.session.commit()

                success_message += str(product.id) + ', '

                print('listed')
                print('---------------------')

            except:
                error = True
                error_message += str(product.id) + ', '

        i+=1
print(counter)

