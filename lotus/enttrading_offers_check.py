# -*- coding: utf-8 -*-

from lotus import *
import csv

p_ids = []

days = [datetime.now().strftime('%Y_%m_%d')]
for day in days:
    write_filename = '/home/lotus/lager/Enttrading_' + day + '.csv'
    i=0
    new_products = []
    new_release = []
    with open(write_filename, encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=';', dialect=csv.excel)
        for row in csv_reader:
            if i == 0:
                i += 1
                for key in row:
                    print(key)
                print('-----------')
            hsp_id = row['ean']
            if hsp_id:
                while len(hsp_id) < 13:
                    hsp_id = '0' + hsp_id
            else:
                continue
            p = Product.query.filter_by(hsp_id=hsp_id).first()
            if p is not None:
                print(i)
                i += 1
                p.weight = str_to_float(money_to_float(row['weight_g'])) / 1000
                db.session.commit()
                print('-----------------------------')