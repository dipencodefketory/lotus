# -*- coding: utf-8 -*-

from lotus import env_vars_path
import xml.etree.ElementTree as ETree
from os import environ
from dotenv import load_dotenv
import requests


def escape_cdata(text):
    # escape character data
    try:
        if not text.startswith("<![CDATA[") and not text.endswith("]]>"):
            if "&" in text:
                text = text.replace("&", "&amp;")
            if "<" in text:
                text = text.replace("<", "&lt;")
            if ">" in text:
                text = text.replace(">", "&gt;")
        return text
    except (TypeError, AttributeError):
        ETree._raise_serialization_error(text)


ETree._escape_cdata = escape_cdata
load_dotenv(env_vars_path)
url = "https://api.afterbuy.de/afterbuy/ABInterface.aspx"


def add_node(name: str, value, parent):
    el = ETree.SubElement(parent, name)
    el.text = f'<![CDATA[{value}]]>'
    return None


def construct_xml_header(call: str, err_lang: str = 'DE', detail_level: int = None, max_shop_items: int = None, request_all_items: int = None):
    xml_tree = ETree.Element('Request')
    ab_global = ETree.SubElement(xml_tree, 'AfterbuyGlobal')
    add_node('PartnerID', environ.get('AFTERBUY_PARTNER_ID'), ab_global)
    add_node('PartnerPassword', environ.get('AFTERBUY_PARTNER_PASSWORD'), ab_global)
    add_node('UserID', environ.get('AFTERBUY_USER_ID'), ab_global)
    add_node('UserPassword', environ.get('AFTERBUY_USER_PASSWORD'), ab_global)
    add_node('CallName', call, ab_global)
    add_node('ErrorLanguage', err_lang, ab_global)
    add_node('DetailLevel', detail_level, ab_global) if detail_level is not None else None
    add_node('MaxShopItems', max_shop_items, xml_tree) if max_shop_items is not None else None
    add_node('RequestAllItems', request_all_items, xml_tree) if request_all_items is not None else None
    return xml_tree


def get_sold_items(filters: dict):
    if type(filters) != dict:
        raise TypeError(f'Variable filters must be of type dict.')
    else:
        xml_tree = construct_xml_header('GetSoldItems', request_all_items=0)
        data_filters = ETree.SubElement(xml_tree, 'DataFilter')
        for filter_name in filters:
            if filter_name in ['DateFilter', 'OrderID', 'Plattform', 'RangeID', 'DefaultFilter', 'AfterbuyUserID', 'UserDefinedFlag', 'AfterbuyUserEmail', 'FilterValue', 'Tag']:
                data_filter = ETree.SubElement(data_filters, 'Filter')
                add_node('FilterName', filter_name, data_filter)
                filter_values = ETree.SubElement(data_filter, 'FilterValues')
                if filter_name == 'DateFilter':
                    add_node('FilterValue', filters[filter_name][0], filter_values)
                    add_node('DateFrom', filters[filter_name][1], filter_values)
                    add_node('DateTo', filters[filter_name][2], filter_values)
                elif filter_name == 'RangeID':
                    add_node('ValueFrom', filters[filter_name][0], filter_values)
                    add_node('ValueTo', filters[filter_name][1], filter_values)
                else:
                    for el in filters[filter_name]:
                        add_node('FilterValue', el, filter_values)
            else:
                raise ValueError(f'Unknown filter with name "{filter_name}".')
        xml_str = ETree.tostring(xml_tree, encoding='utf-8', method='xml')
        return requests.get(url, data=xml_str, headers={'Content-Type': 'application/xml; charset=utf-8'})


def update_sold_items(orders: list):
    xml_tree = construct_xml_header('UpdateSoldItems')
    order_tree = ETree.SubElement(xml_tree, 'Orders')
    for o in orders:
        order = ETree.SubElement(order_tree, 'Order')
        add_node('OrderID', o['order_id'], order) if 'order_id' in o else None
        add_node('ItemID', o['item_id'], order) if 'item_id' in o else None
        add_node('UserDefinedFlag', o['user_defined_flag'], order) if 'user_defined_flag' in o else None
        add_node('AdditionalInfo', o['additional_info'], order) if 'additional_info' in o else None
        add_node('MailDate', o['mail_date'], order) if 'mail_date' in o else None
        add_node('ReminderMailDate', o['reminder_mail_date'], order) if 'reminder_mail_date' in o else None
        add_node('UserComment', o['user_comment'], order) if 'user_comment' in o else None
        add_node('OrderMemo', o['order_memo'], order) if 'order_memo' in o else None
        add_node('InvoiceMemo', o['invoice_memo'], order) if 'invoice_memo' in o else None
        add_node('InvoiceNumber', o['invoice_number'], order) if 'invoice_number' in o else None
        add_node('OrderExported', o['order_exported'], order) if 'order_exported' in o else None
        add_node('InvoiceDate', o['invoice_date'], order) if 'invoice_date' in o else None
        add_node('HideOrder', o['hide_order'], order) if 'hide_order' in o else None
        add_node('Reminder1Date', o['reminder1_date'], order) if 'reminder1_date' in o else None
        add_node('Reminder2Date', o['reminder2_date'], order) if 'reminder2_date' in o else None
        add_node('FeedbackDate', o['feedback_date'], order) if 'feedback_date' in o else None
        add_node('ProductID', o['product_id'], order) if 'product_id' in o else None
        if ('use_shipping_address' in o or
                'first_name' in o or
                'last_name' in o or
                'company' in o or
                'street' in o or
                'postal_code' in o or
                'city' in o or
                'country' in o):
            buyer_info = ETree.SubElement(order, 'BuyerInfo')
            shipping_address = ETree.SubElement(buyer_info, 'ShippingAddress')
            add_node('UseShippingAddress', o['use_shipping_address'], shipping_address) if 'use_shipping_address' in o else None
            add_node('FirstName', o['first_name'], shipping_address) if 'first_name' in o else None
            add_node('LastName', o['last_name'], shipping_address) if 'last_name' in o else None
            add_node('Company', o['company'], shipping_address) if 'company' in o else None
            add_node('Street', o['street'], shipping_address) if 'street' in o else None
            add_node('PostalCode', o['postal_code'], shipping_address) if 'postal_code' in o else None
            add_node('City', o['city'], shipping_address) if 'city' in o else None
            add_node('Country', o['country'], shipping_address) if 'country' in o else None
        if ('payment_method' in o or
                'payment_date' in o or
                'already_paid' in o or
                'payment_additional_cost' in o or
                'send_payment_mail' in o):
            payment_info = ETree.SubElement(order, 'PaymentInfo')
            add_node('PaymentMethod', o['payment_method'], payment_info) if 'payment_method' in o else None
            add_node('PaymentDate', o['payment_date'], payment_info) if 'payment_date' in o else None
            add_node('AlreadyPaid', o['already_paid'], payment_info) if 'already_paid' in o else None
            add_node('PaymentAdditionalCost', o['payment_additional_cost'], payment_info) if 'payment_additional_cost' in o else None
            add_node('SendPaymentMail', o['send_payment_mail'], payment_info) if 'send_payment_mail' in o else None
        if ('shipping_method' in o or
                'shipping_group' in o or
                'shipping_cost' in o or
                'delivery_date' in o or
                'ebay_shipping_cost' in o or
                'send_shipping_mail' in o or
                'delivery_service' in o):
            shipping_info = ETree.SubElement(order, 'ShippingInfo')
            add_node('ShippingMethod', o['shipping_method'], shipping_info) if 'shipping_method' in o else None
            add_node('ShippingGroup', o['shipping_group'], shipping_info) if 'shipping_group' in o else None
            add_node('ShippingCost', o['shipping_cost'], shipping_info) if 'shipping_cost' in o else None
            add_node('DeliveryDate', o['delivery_date'], shipping_info) if 'delivery_date' in o else None
            add_node('eBayShippingCost', o['ebay_shipping_cost'], shipping_info) if 'ebay_shipping_cost' in o else None
            add_node('SendShippingMail', o['send_shipping_mail'], shipping_info) if 'send_shipping_mail' in o else None
            add_node('DeliveryService', o['delivery_service'], shipping_info) if 'delivery_service' in o else None
        if ('VorgangsInfo1' in o or
                'VorgangsInfo2' in o or
                'VorgangsInfo3' in o):
            vorgangs_info = ETree.SubElement(order, 'VorgangsInfo')
            add_node('VorgangsInfo1', o['vorgangs_info1'], vorgangs_info) if 'vorgangs_info1' in o else None
            add_node('VorgangsInfo2', o['vorgangs_info2'], vorgangs_info) if 'vorgangs_info2' in o else None
            add_node('VorgangsInfo3', o['vorgangs_info3'], vorgangs_info) if 'vorgangs_info3' in o else None
        if 'tags' in o:
            tags = ETree.SubElement(order, 'Tags')
            for tag in o['tags']:
                add_node('Tag', tag, tags)
    xml_str = ETree.tostring(xml_tree, encoding='utf-8', method='xml')
    return requests.get(url, data=xml_str, headers={'Content-Type': 'application/xml; charset=utf-8'})


def get_shop_products(filters: dict):
    if type(filters) != dict:
        raise TypeError(f'Variable filters must be of type dict.')
    else:
        xml_tree = construct_xml_header('GetShopProducts', detail_level=0, request_all_items=0, max_shop_items=250)
        data_filters = ETree.SubElement(xml_tree, 'DataFilter')
        for filter_name in filters:
            if filter_name in ['ProductID', 'Anr', 'Ean', 'Tag', 'DefaultFilter', 'Level', 'RangeID', 'RangeAnr', 'DateFilter']:
                data_filter = ETree.SubElement(data_filters, 'Filter')
                add_node('FilterName', filter_name, data_filter)
                filter_values = ETree.SubElement(data_filter, 'FilterValues')
                if filter_name in ['ProductID', 'Anr', 'Ean', 'Tag', 'DefaultFilter']:
                    if filter_name == 'DefaultFilter' and filters[filter_name][0] not in ['AllSets', 'VariationsSets', 'ProductSets', 'not_AllSets', 'not_VariationsSets', 'not_ProductSets']:
                        raise ValueError(f'Unknown filter_name "{filters[filter_name][0]}".')
                    else:
                        for el in filters[filter_name]:
                            add_node('FilterValue', el, filter_values)
                elif filter_name == 'Level':
                    add_node('LevelFrom', filters[filter_name][0], filter_values)
                    add_node('LevelTo', filters[filter_name][1], filter_values)
                elif filter_name in ['RangeID', 'RangeAnr']:
                    add_node('ValueFrom', filters[filter_name][0], filter_values)
                    add_node('ValueTo', filters[filter_name][1], filter_values)
                elif filter_name == 'DateFilter':
                    if filters[filter_name][0] not in ['ModDate', 'LastSale']:
                        raise ValueError(f'Unknown filter_name "{filters[filter_name][0]}".')
                    else:
                        add_node('FilterValue', filters[filter_name][0], filter_values)
                        add_node('DateFrom', filters[filter_name][1], filter_values)
                        add_node('DateTo', filters[filter_name][2], filter_values)
            else:
                raise ValueError(f'Unknown filter with name "{filter_name}".')
        xml_str = ETree.tostring(xml_tree, encoding='utf-8', method='xml')
        return requests.get(url, data=xml_str, headers={'Content-Type': 'application/xml; charset=utf-8'})


def update_shop_products(product_tree: ETree):
    xml_tree = construct_xml_header('UpdateShopProducts')
    xml_tree.append(product_tree)
    xml_str = ETree.tostring(xml_tree, encoding='utf-8', method='xml')
    return requests.get(url, data=xml_str, headers={'Content-Type': 'application/xml; charset=utf-8'})


def get_lister_history(filters: dict):
    if type(filters) != dict:
        raise TypeError(f'Variable filters must be of type dict.')
    else:
        xml_tree = construct_xml_header('GetListerHistory', detail_level=0, request_all_items=0, max_shop_items=250)
        data_filters = ETree.SubElement(xml_tree, 'DataFilter')
        for filter_name in filters:
            if filter_name in ['HistoryID', 'Anr', 'RangeID', 'RangeAnr', 'StartDate', 'EndDate', 'Plattform', 'ListingType', 'AccountID', 'SiteID']:
                data_filter = ETree.SubElement(data_filters, 'Filter')
                add_node('FilterName', filter_name, data_filter)
                filter_values = ETree.SubElement(data_filter, 'FilterValues')
                if filter_name in ['Anr']:
                    for el in filters[filter_name]:
                        add_node('FilterValue', el, filter_values)
                else:
                    raise ValueError(f'Filter with name "{filter_name}" not yet implemented.')
            else:
                raise ValueError(f'Unknown filter with name "{filter_name}".')
        xml_str = ETree.tostring(xml_tree, encoding='utf-8', method='xml')
        return requests.get(url, data=xml_str, headers={'Content-Type': 'application/xml; charset=utf-8'})

