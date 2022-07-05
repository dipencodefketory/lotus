from lotus import db
from basismodels import Product, WSRProduct, Sale, PricingLog, Product_Stock_Attributes, WSRParcel, WSReceipt
import pandas as pd
from sqlalchemy import create_engine
import idealo_offer
from datetime import datetime, timedelta

engine = create_engine('postgresql://postgres:Lotus210676!@82.165.244.152/lotus', echo=True)

idealo_df = pd.read_csv('offer_report.csv')

db_df = pd.read_sql(
    """
        SELECT 
            product.internal_id, product_stock_attributes.quantity 
        FROM 
            product JOIN product_stock_attributes ON product.id = product_stock_attributes.product_id
        WHERE
            product_stock_attributes.stock_id = 1
    """,
    con=engine
)
db_df["internal_id"] = db_df["internal_id"].apply(pd.to_numeric)

idealo_df = idealo_df.rename(columns={'SKU': 'internal_id'})

df = pd.merge(db_df, idealo_df, on='internal_id', how='inner')
df = df[df['StockAvailabilityPerDay'] == 0]

df = df[df['quantity'] > 0]

internal_ids = df['internal_id'].apply(str).tolist()

ps = db.session.query(Product).filter(Product.internal_id.in_(internal_ids)).all()
dt = datetime.now()
auth = idealo_offer.get_access_token()
for p in ps:
    if datetime.now() - timedelta(minutes=50) > dt:
        dt = datetime.now()
        authorization = idealo_offer.get_access_token()
    try:
        p.mp_update(marketplace_id=1, quantity=True, authorization=auth)
    except Exception as e:
        print(e)
