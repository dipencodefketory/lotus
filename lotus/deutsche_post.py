# -*- coding: utf-8 -*-

import requests, base64
from requests.auth import HTTPBasicAuth
from datetime import *

"""
max 15 requests per second
max 1 tracking request for specific barcode/awb in 4 hours
"""

url = 'https://api-qa.deutschepost.com/v1/auth/accesstoken'

client_id = 'c96b49bb-c378-4a15-b2e3-842a9850b23d'
client_secret = 'be44af0a-74f9-438e-a3ac-e3e21d84259f'

b64Val = base64.b64encode((client_id+':'+client_secret).encode('utf-8'))

headers = {'Content-Type': 'application/json',
          'Accept': '',
          'Authorization': 'Basic ' + b64Val.decode('utf-8')}

r = requests.get(url, headers=headers, auth=HTTPBasicAuth(client_id, client_secret))

token = r.json()

contactName = 'Faruk Önal'
contact_jobReference = 'CEO'
pickupTypeOptions = ['CUSTOMER_DROP_OFF', 'SCHEDULED', 'DHL_GLOBAL_MAIL', 'DHL_EXPRESS']    # What are those?!
pickupType = pickupTypeOptions[3]
pickupLocation = 'Proskauer Str. 32. 10247 Berlin'
if datetime.now().hour>=12:
    pickupDate = datetime.today()+timedelta(days=1)
else:
    pickupDate = datetime.today()
telephoneNumber = '+493035306768'

customer = {}
order = {}

productOptions = ['GPP', 'GMP', 'GMM', 'GMR', 'GPT']    # What are those?!
product = productOptions[0]

"""
The service level that is used for the shipment of this item. 
There are restrictions for use of service level: 
REGISTERED is only available with product GMR and SalesChannel DPI, 
STANDARD is only available with products GMM and GMP, 
PRIORITY is only available with products GPT, GPP and GMP.
"""

serviceLevelOptions = ['PRIORITY', 'STANDARD', 'REGISTERED']
serviceLevel = serviceLevelOptions[0]

shipmentNaturetypeOptions = ['SALE_GOODS', 'RETURN_GOODS', 'GIFT', 'COMMERCIAL_SAMPLE',
                             'DOCUMENTS', 'MIXED_CONTENTS', 'OTHERS']   # What are those?!
shipmentNaturetype = shipmentNaturetypeOptions[0]

values = {"customerEkp": "6264468434",
          "orderStatus": "FINALIZE",
          "paperwork": {
              "contactName": contactName,
              "awbCopyCount": 3,
              "jobReference": contact_jobReference,
              "pickupType": pickupType,
              "pickupLocation": pickupLocation,
              "pickupDate": pickupDate,
              "pickupTimeSlot": "MIDDAY",
              "telephoneNumber": telephoneNumber
          },
          "items": [
              {
                  "product": product,                                                   #required
                  "serviceLevel": serviceLevel,
                  "recipient": customer['recipient'],                                   #required
                  "addressLine1": customer['addressLine1'],                             #required
                  "city": customer['city'],                                             #required
                  "destinationCountry": customer['destinationCountry'],                 #required
                  "custRef": customer['custRef'],
                  "recipientPhone": customer['recipientPhone'],
                  "recipientFax": customer['recipientFax'],
                  "recipientEmail": customer['recipientEmail'],
                  "addressLine2": customer['addressLine2'],
                  "addressLine3": customer['addressLine3'],
                  "state": customer['state'],
                  "postalCode": customer['postalCode'],
                  "shipmentAmount": order['shipmentAmount'],
                  "shipmentCurrency": order['shipmentCurrency'],
                  "shipmentGrossWeight": order['shipmentGrossWeight'],                  #required
                  "returnItemWanted": order['returnItemWanted'],
                  "shipmentNaturetype": shipmentNaturetype,
                  "contents": [
                      {
                          "contentPieceHsCode": order['contentPieceHsCode'],            #required
                          "contentPieceDescription": order['contentPieceDescription'],  #required
                          "contentPieceValue": order['contentPieceValue'],              #required
                          "contentPieceNetweight": order['contentPieceNetweight'],      #required
                          "contentPieceOrigin": order['contentPieceOrigin'],            #required
                          "contentPieceAmount": order['contentPieceAmount']             #required
                      }
                  ]
              }
          ]
          }

headers = {'Content-Type': 'application/json',
           'Accept': 'application/json',
           'Authorization': 'Bearer '+token,
           'ThirdPartyVendor-ID': ''
           }

r = requests.post('https://api-qa.deutschepost.com/dpi/shipping/v1/orders', data=values, headers=headers)

print(r.text)
