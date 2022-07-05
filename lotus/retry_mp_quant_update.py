import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import ast

from lotus import db
from basismodels import Product
import idealo_offer


idealo_auth = idealo_offer.get_access_token()


engine = create_engine('postgresql://postgres:Lotus210676!@82.165.244.152/lotus')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()
con = session.get_bind()

query = """
SELECT 
    p.id AS product_id,
    mpa.marketplace_id AS marketplace_id,
    sq_1.data
FROM
    marketplace_product_attributes mpa JOIN 
    product p ON p.id = mpa.product_id JOIN 
    product_stock_attributes psa ON psa.product_id = p.id JOIN 
    (
        SELECT
            pul.product_id AS p_id,
            pul.marketplace_id AS mp_id,
            pul.data AS data
        FROM
            product_update_log pul JOIN 
            (
                SELECT
                    pul.id AS pul_id,
                    RANK() OVER (PARTITION BY pul.product_id, pul.marketplace_id ORDER BY pul.init_date DESC) AS rnk
                FROM 
                    product_update_log pul
                WHERE
                    pul.status_code IN (200, 204) AND
                    (
                        pul.data LIKE '%checkoutLimitPerPeriod%' OR pul.data LIKE '%availableQuantity%'
                    )
            ) sq_2 ON sq_2.pul_id = pul.id
        WHERE
            sq_2.rnk = 1
    ) sq_1 ON (sq_1.p_id = psa.product_id) AND (sq_1.mp_id = mpa.marketplace_id)
WHERE
    psa.stock_id = 1 AND
    psa.quantity > 0 AND
    mpa.max_stock > 0 AND
    mpa.upload_clearance = TRUE
"""

df = pd.read_sql(query, con=con)
df.data = df.data.apply(ast.literal_eval)
df['upload_quant'] = df.data.apply(lambda x: x['checkoutLimitPerPeriod'] if 'checkoutLimitPerPeriod' in x else x['availableQuantity'])
df = df.loc[df.upload_quant == 0]
print(df.head)
print(df.columns)

# Idealo-retry
idealo_ids = list(df.loc[df.marketplace_id == 1]['product_id'])
products = db.session.query(
    Product
).filter(
    Product.id.in_(idealo_ids)
).all()

le = len(products)
start = datetime.now()
for i, (product) in enumerate(products):
    if datetime.now() - timedelta(minutes=50) > start:
        start = datetime.now()
        idealo_auth = idealo_offer.get_access_token()
    print('-----------------------')
    print(f'{i}/{le}')
    print(product.id)
    try:
        r = product.mp_update(1, shipping_time=True, quantity=True, authorization=idealo_auth)
        print(r)
    except Exception as e:
        print(e)


# Ebay-retry
ebay_ids = list(df.loc[df.marketplace_id == 2]['product_id'])
products = db.session.query(
    Product
).filter(
    Product.id.in_(ebay_ids)
).all()

le = len(products)
for i, (product) in enumerate(products):
    print('-----------------------')
    print(f'{i}/{le}')
    print(product.id)
    try:
        r = product.mp_update(2, shipping_time=True, quantity=True)
        print(r)
    except Exception as e:
        print(e)



