from lotus import *
import ftplib
from datetime import *
import os
from typing import List
from lookup import comma_split_features
import html2text
from PIL import Image

h = html2text.HTML2Text()
h.body_width = 0


def feature_value_adder(product, feature_name: str, feature_values: List[str], source: str):
    if feature_name and feature_values:
        feature = ProductFeature.query.filter_by(name=feature_name, source=source).first()
        if feature is None:
            feature = ProductFeature(None, feature_name, False)
            feature.source = source
            db.session.add(feature)
            db.session.commit()
        for value in feature_values:
            value = value.strip()
            if value:
                feature_value = ProductFeatureValue.query.filter_by(value=value, productfeature_id=feature.id).first()
                if feature_value is None:
                    feature_value = ProductFeatureValue(value, feature.id)
                    db.session.add(feature_value)
                    db.session.commit()

                if product not in feature_value.get_products():
                    db.session.add(Product_ProductFeatureValue(product.id, feature_value.id))
                    db.session.commit()
        return 200
    else:
        return 400


filename = 'Vitrex_Artikelstamm_Bilder.csv'
write_filename = '/home/lotus/lager/Vitrex_' + datetime.now().strftime('%Y_%m_%d') + '.csv'

ftp = ftplib.FTP("80.147.95.142")
ftp.login("40790", "vtyh3VJD")
ftp.retrbinary("RETR " + filename, open(write_filename, 'wb').write)
ftp.quit()

req_response = ''
error_message = 'Beim Upload der folgenden Produkte sind Fehler entstanden:\n'
error = False

success_message = 'Die Produkte mit den IDs '

vitrex_link_cat = ProductLinkCategory.query.filter_by(id=5).first()
own_stock = Stock.query.filter_by(owned=True).first()

counter = 0
error_rows = []
with open(write_filename, encoding='cp1252') as csv_file:
    csv_reader = csv.DictReader(csv_file, delimiter=';', dialect=csv.excel)
    i=0
    new_products = []
    new_release = []
    for row in csv_reader:
        if i==0:
            i+=1
            continue
        if row['Genre'] in ['BuchHeft', 'Code-Card', 'Guthaben Karte Online', 'Merchandise', 'Spielzeug', '']:
            counter +=1
            continue

        internal_id = row['Art.Nr']
        prod_hsp_id = row['EAN'].strip()
        prod_name = row['Titel'].strip().replace('    ', ' - ').replace('   ', ' - ').replace('  ', ' - ')

        try:
            if prod_hsp_id == '' or prod_hsp_id.isnumeric()==False:
                prod_hsp_id = internal_id
            while len(prod_hsp_id) < 13:
                prod_hsp_id = '0' + prod_hsp_id

            if len(prod_name)>70:
                prod_name = prod_name[:70].rsplit(' ', 1)[0]
            prod_brand = row['Label'].replace('    ', ' - ').replace('   ', ' - ').replace('  ', ' - ')

            prod_quant = int(row['Bestand'])
            prod_tax = 19
            prod_price = float(row['EK-Preis'].replace(',', '.'))

            release_date = row['VÖ-Datum']

            k=0
            while len(prod_hsp_id) > 13 and prod_hsp_id[0]=='0' and k<10:
                prod_hsp_id = prod_hsp_id[1:]
                k+=1
            product = Product.query.filter_by(hsp_id=prod_hsp_id).first()
            supplier = Supplier.query.filter_by(firmname='Vitrex').first()
            vitrex = Stock.query.filter_by(supplier_id=supplier.id, name='Angebote').first()
            if not product:
                psa = Product_Stock_Attributes.query.filter_by(stock_id=vitrex.id, internal_id=internal_id).order_by(Product_Stock_Attributes.termination_date).first()
                if psa:
                    product = psa.product
                    product.hsp_id = prod_hsp_id
                    product.release_date = datetime.strptime(release_date, '%d.%m.%Y')
                    db.session.commit()
                    psa = Product_Stock_Attributes('Neu & OVP', prod_quant, prod_price, None, prod_tax, None, datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                                                   datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999), product.id, vitrex.id, internal_id=internal_id)
                    psa.last_seen = datetime.now()
                    db.session.add(psa)
                    db.session.commit()
        except Exception as e:
            print(e)
