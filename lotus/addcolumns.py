from lotus import db, text

'''
sql = text('ALTER TABLE productfeaturevalue '
           'ADD COLUMN int_value_id integer, '
           'add constraint fk_int_value_id '
           'foreign key (int_value_id) '
           'references productfeaturevalue (id);'
           )

sql = text('ALTER TABLE marketplace_product_attributes ALTER COLUMN name TYPE character varying(255);'
           )
           
sql = text('ALTER TABLE product '
           'ADD COLUMN release_date timestamp without time zone;'
           )
           
sql = text('ALTER TABLE marketplace_product_attributes '
           'ADD COLUMN block_selling_price BOOLEAN;'
           )

sql = text('ALTER TABLE product ALTER COLUMN name TYPE character varying(255);')

sql = text('ALTER TABLE product_stock_attributes '
           'ADD COLUMN user_generated BOOLEAN;'
           )

sql = text('ALTER TABLE preorder '
           'ADD COLUMN sales integer;'
           )

sql = text('ALTER TABLE product_stock_attributes '
           'ADD COLUMN internal_id character varying(100);'
           )

sql = text('ALTER TABLE marketplace_product_attributes ALTER COLUMN search_term TYPE character varying(255);')

sql = text('ALTER TABLE product '
           'ADD COLUMN currprocstat_id integer, '
           'add constraint fk_int_value_id '
           'foreign key (int_value_id) '
           'references productfeaturevalue (id);'
           )

sql = text('ALTER TABLE productfeaturevalue ALTER COLUMN value TYPE character varying(8191);')


sql = text('ALTER TABLE marketplace_product_attributes '
           'ADD COLUMN category_path character varying(511);'
           )

sql = text('ALTER TABLE product '
           'ADD COLUMN spec_trait_3 character varying(100);'
           )

sql = text('ALTER TABLE "order" '
           'ADD COLUMN sent BOOLEAN;'
           )

sql = text('ALTER TABLE product_stock_attributes '
           'ADD COLUMN sku character varying(20);'
           )

sql = text('ALTER TABLE supplier '
           'ALTER COLUMN std_tax TYPE character varying(20);'
           )

sql = text('ALTER TABLE product '
           'ADD COLUMN cheapest_buying_price float;'
           )

sql = text('ALTER TABLE product '
           'ADD COLUMN cheapest_stock_id integer, '
           'add constraint fk_cheapest_stock_id '
           'foreign key (cheapest_stock_id) '
           'references product_stock_attributes (id);'
           )

for el in ['nat_shipping_2_id', 'nat_shipping_3_id', 'nat_shipping_4_id', 'int_shipping_1_id', 'int_shipping_2_id', 'int_shipping_3_id', 'int_shipping_4_id']:
    q = f"""ALTER TABLE product 
    ADD COLUMN {el} integer, 
    add constraint fk_{el} 
    foreign key ({el}) 
    references shipping_service (id);"""
    sql = text(q)
    query = db.engine.execute(sql)
sql = text('ALTER TABLE marketplace_product_attributes '
           'ADD COLUMN update_price FLOAT;'
           )
db.engine.execute(sql)

sql = text('ALTER TABLE daily_report '
           'ADD COLUMN sellable INTEGER;'
           )
db.engine.execute(sql)


db.engine.execute(sql)

db.engine.execute(sql)

sql = text('ALTER TABLE product '
           'ALTER COLUMN update_psa TYPE BOOLEAN '
           'USING NULL;'
           )

for col in ['own_stock', 'short_sell', 'pre_order']:

    sql = text(f'ALTER TABLE sale ADD COLUMN {col} BOOLEAN;')


sql = text('UPDATE sale SET own_stock=TRUE;')

sql = text('ALTER TABLE product_group DROP CONSTRAINT fk_parent_id;')



sql = text('ALTER TABLE product_group '
           'add constraint fk_parent_id '
           'foreign key (parent_id) '
           'references product_group (id);'
           )


sql = text('ALTER TABLE prd_global_id '
           'RENAME COLUMN init_date_time TO init_dt;'
           )

db.engine.execute(sql)


sql = text('select * from information_schema.table_constraints; '
           )

r = db.engine.execute(sql)
for row in r:
    print(row)

sql = text('ALTER TABLE prd_global_id DROP CONSTRAINT prd_global_id_global_id_key;'
           )

sql = text('ALTER TABLE wsr_product '
           'ADD COLUMN wsr_parcel_id integer, '
           'add constraint fk_wsr_parcel_id '
           'foreign key (wsr_parcel_id) '
           'references wsr_parcel (id);'
           )

'''

for col_name, col_type in [('sku', 'CHARACTER VARYING(20)'), ('ean', 'CHARACTER VARYING(13)'), ('init_dt', 'TIMESTAMP WITHOUT TIME ZONE'), ('weight_g', 'INTEGER'), ('length_mm', 'INTEGER'),
                           ('width_mm', 'INTEGER'), ('height_mm', 'INTEGER'), ('search_mode', 'CHARACTER VARYING(13)'), ('proc_status', 'CHARACTER VARYING(13)'), ('processed', 'BOOLEAN'),
                           ('proc_user_id', 'INTEGER'), ('proc_dt', 'TIMESTAMP WITHOUT TIME ZONE'), ('confirmed', 'BOOLEAN'), ('conf_user_id', 'INTEGER'), ('conf_dt', 'TIMESTAMP WITHOUT TIME ZONE'),
                           ('review', 'BOOLEAN'), ('review_dt', 'TIMESTAMP WITHOUT TIME ZONE'), ('review_user_id', 'INTEGER'), ('quantity', 'INTEGER'),  ('cost', 'FLOAT'), ('drop_sale', 'BOOLEAN'),
                           ('min_cost', 'FLOAT'), ('min_cost_offer_id', 'INTEGER')]:
    sql = text('ALTER TABLE '
               'product '
               'ADD COLUMN '
               f'{col_name} {col_type};'
               )
    print(sql)
    db.engine.execute(sql)
