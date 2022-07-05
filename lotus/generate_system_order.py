# -*- coding: utf-8 -*-

from lotus import *


supplier = Supplier.query.filter_by(firmname='Lager').first()
last_system_order = Order.query.filter_by(supplier_id=supplier.id, name='Nullbestellung').order_by(Order.order_time.desc()).first()
order_time = last_system_order.order_time
own_stock = Stock.query.filter_by(owned=True).first()
payment_method = PaymentMethod.query.filter_by(name='-').first()
neworder = Order('Nullbestellung', datetime.now(), datetime.now(), None, 0, None, own_stock.id, payment_method.id, supplier.id)
db.session.add(neworder)
db.session.commit()
summed_cost = 0

products = Product.query.order_by(Product.id).all()

url = "https://api.afterbuy.de/afterbuy/ABInterface.aspx"
request_quant = 250
i = 1
while i * request_quant < len(products):
    print(i)
    xml = """<?xml version="1.0" encoding="utf-8"?>
        <Request>
            <AfterbuyGlobal>
                <PartnerID><![CDATA[1000007048]]></PartnerID>
                <PartnerPassword><![CDATA[epK7Ob9QO1geo44zUHqrgPhnU]]></PartnerPassword>
                <UserID><![CDATA[Lotusicafe]]></UserID>
                <UserPassword><![CDATA[210676After251174]]></UserPassword>
                <CallName>GetShopProducts</CallName>
                <DetailLevel>12</DetailLevel>
                <ErrorLanguage>DE</ErrorLanguage>
            </AfterbuyGlobal>
            <MaxShopItems>""" + str(request_quant) + """</MaxShopItems>
            <DataFilter>
            <Filter>
                <FilterName>ProductID</FilterName>
                <FilterValues>\n"""
    for product in products[(i - 1) * request_quant:i * request_quant]:
        xml += """<FilterValue>""" + product.internal_id + """</FilterValue>\n"""
    xml += """</FilterValues>
        </Filter>
        </DataFilter>
        </Request>
        """
    headers = {'Content-Type': 'application/xml'}
    r = requests.get(url, data=xml, headers=headers)

    tree = ET.fromstring(r.text)

    product_query = [item for item in tree.iter() if item.tag == 'Product']
    for prod in product_query:
        prod_id = [item.text for item in prod.iter() if item.tag == 'ProductID'][0]
        quant = [item.text for item in prod.iter() if item.tag == 'AuctionQuantity'][0]
        oth_quant = [item.text for item in prod.iter() if item.tag == 'Quantity'][0]
        if int(quant)+int(oth_quant) != 0:
            product = Product.query.filter_by(internal_id=prod_id).first()
            if product:
                av_bp = product.get_own_buying_price_from(order_time)
                check_products = Product.query.filter_by(hsp_id=product.hsp_id).order_by(Product.internal_id).all()
                n = len(check_products)
                j = 0
                while av_bp == None and j < n:
                    av_bp = check_products[j].get_own_buying_price_from(order_time)
                    j += 1
                if av_bp == None:
                    print('Kein Ausweich-Produkt mit gleicher EAN gefunden')
                    print(product.id)
                    print('---------------------')
                else:
                    new_order_product_attributes = Order_Product_Attributes(int(quant)+int(oth_quant), int(quant)+int(oth_quant), av_bp, 19, neworder.id, product.id)
                    summed_cost += (int(quant) + int(oth_quant)) * av_bp
                    db.session.add(new_order_product_attributes)
                    db.session.commit()
    i += 1

xml = """<?xml version="1.0" encoding="utf-8"?>
            <Request>
                <AfterbuyGlobal>
                    <PartnerID><![CDATA[1000007048]]></PartnerID>
                    <PartnerPassword><![CDATA[epK7Ob9QO1geo44zUHqrgPhnU]]></PartnerPassword>
                    <UserID><![CDATA[Lotusicafe]]></UserID>
                    <UserPassword><![CDATA[210676After251174]]></UserPassword>
                    <CallName>GetShopProducts</CallName>
                    <DetailLevel>12</DetailLevel>
                    <ErrorLanguage>DE</ErrorLanguage>
                </AfterbuyGlobal>
                <MaxShopItems>""" + str(request_quant) + """</MaxShopItems>
                <DataFilter>
                <Filter>
                    <FilterName>ProductID</FilterName>
                    <FilterValues>\n"""
for product in products[(i - 1) * request_quant:i * request_quant]:
    xml += """<FilterValue>""" + product.internal_id + """</FilterValue>\n"""
xml += """</FilterValues>
            </Filter>
            </DataFilter>
            </Request>
            """
headers = {'Content-Type': 'application/xml'}
r = requests.get(url, data=xml, headers=headers)

tree = ET.fromstring(r.text)

product_query = [item for item in tree.iter() if item.tag == 'Product']
for prod in product_query:
    prod_id = [item.text for item in prod.iter() if item.tag == 'ProductID'][0]
    quant = [item.text for item in prod.iter() if item.tag == 'AuctionQuantity'][0]
    oth_quant = [item.text for item in prod.iter() if item.tag == 'Quantity'][0]
    if int(quant) + int(oth_quant) != 0:
        product = Product.query.filter_by(internal_id=prod_id).first()
        if product:
            av_bp = product.get_own_buying_price_from(order_time)
            check_products = Product.query.filter_by(hsp_id=product.hsp_id).order_by(Product.internal_id).all()
            n = len(check_products)
            j = 0
            while av_bp == None and j < n:
                av_bp = check_products[j].get_own_buying_price_from(order_time)
                j += 1
            if av_bp == None:
                print('Kein Ausweich-Produkt mit gleicher EAN gefunden')
                print(product.id)
                print('---------------------')
            else:
                new_order_product_attributes = Order_Product_Attributes(int(quant) + int(oth_quant), int(quant) + int(oth_quant), av_bp, 19, neworder.id, product.id)
                summed_cost += (int(quant) + int(oth_quant)) * av_bp
                db.session.add(new_order_product_attributes)
                db.session.commit()

newlog = ShippingStatus_Log(2, 'abgeschlossen', '', neworder.id)
newlog.init_date = datetime.now()
db.session.add(newlog)
db.session.commit()
neworder.price = summed_cost
db.session.commit()

url = "https://api.afterbuy.de/afterbuy/ABInterface.aspx"
request_quant = 250
i = 1
while i * request_quant < len(products):
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
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
                                    <Products>\n'''
    for product in products[(i - 1) * request_quant:i * request_quant]:
        try:
            xml += '''<Product>
                                        <ProductIdent>
                                            <ProductInsert>0</ProductInsert>
                                            <ProductID><![CDATA[''' + product.internal_id + ''']]></ProductID>
                                        </ProductIdent>
                                        <BuyingPrice>''' + float_to_comma(float(("%.2f" % product.get_own_buying_price()))) + '''</BuyingPrice>
                                    </Product>\n'''
        except:
            pass
    xml += '''</Products>
                        </Request>'''

    xml = xml.encode('utf-8')

    headers = {'Content-Type': 'application/xml; charset=utf-8'}
    requests.get(url, data=xml, headers=headers)

    i += 1

xml = '''<?xml version="1.0" encoding="UTF-8"?>
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
                                <Products>\n'''
for product in products[(i - 1) * request_quant:i * request_quant]:
    try:
        xml += '''<Product>
                                    <ProductIdent>
                                        <ProductInsert>0</ProductInsert>
                                        <ProductID><![CDATA[''' + product.internal_id + ''']]></ProductID>
                                    </ProductIdent>
                                    <BuyingPrice>''' + float_to_comma(float(("%.2f" % product.get_own_buying_price()))) + '''</BuyingPrice>
                                </Product>\n'''
    except:
        pass
xml += '''</Products>
                    </Request>'''
i += 1

xml = xml.encode('utf-8')

headers = {'Content-Type': 'application/xml; charset=utf-8'}
requests.get(url, data=xml, headers=headers)