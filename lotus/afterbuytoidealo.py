# -*- coding: utf-8 -*-

from lotus import *
from datetime import *
from idealo_order import set_fulfil_info, get_access_token
import csv

script_start = datetime.now()

url = "https://api.afterbuy.de/afterbuy/ABInterface.aspx"
n=3
i=0
while i<=n:
    start = (datetime.now()-timedelta(days=n-i)).strftime('%d.%m.%Y')
    print(start)
    i+=1
    end = datetime.now().strftime('%d.%m.%Y')

    xml="""<?xml version="1.0" encoding="utf-8"?>
    <Request>
      <AfterbuyGlobal>
        <PartnerID><![CDATA[1000007048]]></PartnerID>
        <PartnerPassword><![CDATA[epK7Ob9QO1geo44zUHqrgPhnU]]></PartnerPassword>
        <UserID><![CDATA[Lotusicafe]]></UserID>
        <UserPassword><![CDATA[210676After251174]]></UserPassword>
        <CallName>GetSoldItems</CallName>
        <DetailLevel>28</DetailLevel>
        <ErrorLanguage>DE</ErrorLanguage>
      </AfterbuyGlobal>
      <RequestAllItems>0</RequestAllItems>
      <DataFilter>
       <Filter>
         <FilterName>DateFilter</FilterName>
         <FilterValues>
           <DateFrom>"""+ start + """ 00:00:00</DateFrom>
           <DateTo>"""+ start +""" 23:59:59</DateTo>
           <FilterValue>AuctionEndDate</FilterValue>
         </FilterValues>
        </Filter>
       <Filter>
         <FilterName>Tag</FilterName>
         <FilterValues>
           <FilterValue>Idealo</FilterValue>
         </FilterValues>
        </Filter>
      </DataFilter>
    </Request>
    """

    headers = {'Content-Type': 'application/xml'}
    r = requests.get(url, data=xml, headers=headers)

    soup = BS(r.text, 'xml')

    #Real
    name = '/home/lotus/logs/afterbuy_to_idealo/' + script_start.strftime('%Y%m%d_%H%M') + '.csv'
    #name = script_start.strftime('%Y%m%d_%H%M') + '.csv'

    access_dict = get_access_token()

    with open(name, 'w', newline='') as csvfile:
        idealo_order_numbers = None
        first_row = ['order_id', 'tracking_number', 'carrier', 'status_code']
        spamwriter = csv.writer(csvfile, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(first_row)

        for order in soup.find_all('Order'):
            idealo_order_number = ''
            # Adding Sale to DB
            shipping_price = str_to_float(money_to_float(order.ShippingTotalCost.text))
            if order.ShippingMethod:
                shipping_method = order.ShippingMethod.text
            else:
                shipping_method = None
            if order.AdditionalInfo:
                tracking_code = order.AdditionalInfo.text
            else:
                tracking_code = None
            timestamp = datetime.strptime(order.OrderDate.text, '%d.%m.%Y %H:%M:%S')
            if order.Tag:
                marketplace = Marketplace.query.filter_by(name=order.Tag.text).first()
                if order.Tag.text == 'Idealo':
                    idealo_order_number = order.AlternativeItemNumber1.text
            else:
                marketplace = Marketplace.query.filter_by(name='Ebay').first()
            print(idealo_order_number)
            print(tracking_code)
            # Sending Trackingnumber to Idealo
            if idealo_order_number and tracking_code:
                carrier_dict = {'de_DHLPaket': 'DHL', 'DE_DHLPaket': 'DHL', 'DE_DHLAlterssichtprüfung18': 'DHL'}
                if shipping_method in carrier_dict:
                    r = set_fulfil_info(access_dict, idealo_order_number, carrier_dict[shipping_method], tracking_code)
                    spamwriter.writerow([idealo_order_number, tracking_code, carrier_dict[shipping_method], r.status_code])
                    print(r.text)
                else:
                    print(f'Shipping-method {shipping_method} missing from carrier dict {carrier_dict}.')
                    spamwriter.writerow([idealo_order_number, tracking_code, shipping_method, 'shipping_method not in carrier_dict.'])
        script_end = datetime.now()
        spamwriter.writerow(['start: ' + script_start.strftime('%d.%m.%Y - %H:%M:%S')])
        spamwriter.writerow(['end: ' + script_end.strftime('%d.%m.%Y - %H:%M:%S')])
        spamwriter.writerow(['runtime: ' + str((script_end-script_start).seconds) + ' seconds'])
