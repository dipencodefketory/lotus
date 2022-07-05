# -*- coding: utf-8 -*-

from lotus import db, Product, Marketplace_Product_Attributes, Product_CurrProcStat, ProductLink, ProductLinkCategory
from product_processor import proc_product
from sqlalchemy import or_, and_


id_cat = ProductLinkCategory.query.filter_by(name='Idealo').first()
p_links = db.session.query(
    ProductLink.product_id
).filter_by(
    category_id=id_cat.id
).filter(
    ProductLink.link.like('%OffersOfProduct%')
).order_by(
    ProductLink.product_id.desc()
).all()

proc_prods = db.session.query(Product_CurrProcStat.product_id).filter(Product_CurrProcStat.proc_user_id==None)

not_listed_ids = db.session.query(Marketplace_Product_Attributes.product_id).filter_by(marketplace_id=2, uploaded=False)

p_ids = []

ps = Product.query.filter(
    and_(or_(Product.state==0,
             Product.state==1),
         Product.id.in_(proc_prods))
).filter(
    Product.id.in_(not_listed_ids)
).filter(
    Product.id.in_(p_links)
).filter(
    Product.id.in_(p_ids) if p_ids else True
).filter(
    Product.id < 10000000
).order_by(
    Product.id.desc()
).limit(15000).all()

processed = []
fallback = []
errors = []
i=0

for p in ps:
    i+=1
    print(i)
    print(p.id)
    print('--------------')
    try:
        a = proc_product(p.id)
        if a == 200:
            processed.append(p.id)
        else:
            fallback.append(p.id)
    except Exception:
        errors.append(p.id)
print('--------------')
print('--------------')
print(f'Processed: {processed}')
print('--------------')
print(f'Fallback: {fallback}')
print('--------------')
print(f'Errors: {errors}')

