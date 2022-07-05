from lotus import *

products = Product.query.order_by(Product.id).filter(Product.id.in_([6917])).all()
request_quant = 250
url = "https://api.afterbuy.de/afterbuy/ABInterface.aspx"

stocks = Stock.query.filter(Stock.owned==False).all()

i=1
while i*request_quant<len(products):
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
        <MaxShopItems>"""+str(request_quant)+"""</MaxShopItems>
        <DataFilter>
        <Filter>
            <FilterName>ProductID</FilterName>
            <FilterValues>\n"""
    for product in products[(i-1)*request_quant:i*request_quant]:
        xml+= """<FilterValue>""" + product.internal_id + """</FilterValue>\n"""
    xml+= """</FilterValues>
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
        product = Product.query.filter_by(internal_id=prod_id).first()

        if product:
            print(product.id)
            stock, buying_price = product.get_cheapest_buying_price_all()
            # noinspection PySimplifyBooleanCheck
            if buying_price:
                continue
            elif product.short_sell == False and int(quant)>90:
                product.short_sell = False
                db.session.commit()

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
                                <Products>
                                    <Product>
                                        <ProductIdent>
                                            <ProductInsert>0</ProductInsert>
                                            <ProductID><![CDATA[''' + product.internal_id + ''']]></ProductID>
                                        </ProductIdent>
                                        <Quantity>0</Quantity>
                                        <AuctionQuantity>''' + str(int(quant)+int(oth_quant)) + '''</AuctionQuantity>
                                        <MergeStock>0</MergeStock>
                                    </Product>
                                </Products>
                            </Request>'''
                headers = {'Content-Type': 'application/xml'}
                r = requests.get(url, data=xml, headers=headers)
    i+=1

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
    product = Product.query.filter_by(internal_id=prod_id).first()

    if product:
        print(product.id)
        stock, buying_price = product.get_cheapest_buying_price_all()
        # noinspection PySimplifyBooleanCheck
        if buying_price:
            continue
        elif product.short_sell == False and int(quant)>90:
            product.short_sell = False
            db.session.commit()

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
                            <Products>
                                <Product>
                                    <ProductIdent>
                                        <ProductInsert>0</ProductInsert>
                                        <ProductID><![CDATA[''' + product.internal_id + ''']]></ProductID>
                                    </ProductIdent>
                                    <Quantity>0</Quantity>
                                    <AuctionQuantity>''' + str(int(quant)+int(oth_quant)) + '''</AuctionQuantity>
                                    <MergeStock>0</MergeStock>
                                </Product>
                            </Products>
                        </Request>'''
            headers = {'Content-Type': 'application/xml'}
            r = requests.get(url, data=xml, headers=headers)
