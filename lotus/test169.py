# -*- coding: utf-8 -*-

from lotus import db
from basismodels import Product, ProductPicture

import ftplib
from PIL import Image
from io import BytesIO
import os


image_count_dict = {}
err = False
ftp = ftplib.FTP('home292546716.1and1-data.host', 'u54225730-night', 'Lotus210676111077!')
for f in ftp.nlst():
    print(f)
    try:
        if 'jpg' in f:
            query = db.session.query(
                ProductPicture, Product
            ).filter(
                Product.id == ProductPicture.product_id
            ).filter(
                ProductPicture.link == f
            ).filter(
                Product.images_taken == True
            ).first()
            if query:
                p, pp = query
                if p.id in image_count_dict:
                    image_count_dict[p.id]['count'] += 1
                else:
                    image_count_dict[p.id] = {'count': 1, 'product': p}
    except Exception as e:
        print(e)
        print(image_count_dict)
        print(image_count_dict.keys())
        err = True
        break
if err is False:
    for key in image_count_dict:
        if image_count_dict[key]['count'] < 2:
            image_count_dict[key]['product'].images_taken = False
            db.session.commit()
