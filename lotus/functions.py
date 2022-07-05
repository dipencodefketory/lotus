# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import decimal
import xml.etree.ElementTree as ETree
from lookup import holidays


def add_node(name: str, value, parent):
    el = ETree.SubElement(parent, name)
    el.text = f'<![CDATA[{value}]]>'
    return None


def check_float(potential_float):
    try:
        float(potential_float)
        return True
    except ValueError:
        return False


def classic_round(val):
    return decimal.Decimal(val).quantize(decimal.Decimal('0.005'), rounding=decimal.ROUND_HALF_UP)


def money_to_float(string):
    string = string.replace(',', '.')
    string = string.replace('"', '')
    string = string.replace("'", "")
    string = string.replace(' ', '')
    string = string.replace('€', '')
    return string


def prc_to_float(string):
    string = string.replace(',', '.')
    string = string.replace('"', '')
    string = string.replace("'", "")
    string = string.replace(' ', '')
    string = string.replace('%', '')
    return string


def working_days_in_range(from_date, to_date):
    from_weekday = from_date.weekday()
    to_weekday = to_date.weekday()
    # If start date is after Friday, modify it to Monday
    add_day = 0
    if from_weekday > 4:
        from_weekday = 0
        add_day = 1
    day_diff = to_weekday - from_weekday
    whole_weeks = ((to_date - from_date).days - day_diff) / 7
    workdays_in_whole_weeks = whole_weeks * 5
    beginning_end_correction = min(day_diff, 5) - (max(to_weekday - 4, 0) % 5)
    working_days = int(workdays_in_whole_weeks + beginning_end_correction)
    # Final sanity check (i.e. if the entire range is weekends)
    return max(0, working_days+add_day)


def add_business_days(from_date, add_days):
    business_days_to_add = add_days
    current_date = from_date
    while business_days_to_add > 0:
        current_date += timedelta(days=1)
        weekday = current_date.weekday()
        if weekday >= 5 or current_date.strftime('%Y-%m-%d') in holidays:
            continue
        business_days_to_add -= 1
    return current_date


def working_days_in_range_2(from_date, to_date):
    if to_date < from_date:
        from_date, to_date = to_date, from_date
    days = 0
    working_days = 0
    while from_date + timedelta(days=days) != to_date:
        days += 1
        current_date = from_date + timedelta(days=days)
        weekday = current_date.weekday()
        if weekday < 5 and current_date.strftime('%Y-%m-%d') not in holidays:
            working_days += 1
    return working_days


def remove_multiples(string, substring):
    while string.count(substring) > 1:
        string = string.replace(substring, "", 1)
    return string


def replacer(string):
    string = remove_multiples(string, 'Nintendo Switch')
    string = remove_multiples(string, 'Switch')
    string = remove_multiples(string, 'Nintendo 3DS')
    string = remove_multiples(string, 'PS4')
    string = remove_multiples(string, 'PlayStation 4')
    string = remove_multiples(string, 'Playstation 4')
    string = remove_multiples(string, 'PlayStation 5')
    string = remove_multiples(string, 'Playstation 5')
    string = remove_multiples(string, 'Switch')
    string = string.replace('Switch', 'Nintendo Switch')
    string = remove_multiples(string, 'Nintendo ')
    string = string.replace('3DS', 'Nintendo 3DS')
    string = string.replace('PC/Mac', 'PC')
    string = string.replace('(Nintendo 3DS)', '- Nintendo 3DS')
    string = string.replace('(Nintendo Switch)', '- Nintendo Switch')
    string = string.replace('(DS)', '- Nintendo DS')
    string = string.replace('(Xbox One)', '- Xbox ONE')
    string = string.replace('Xbox One', 'Xbox ONE')
    string = string.replace('(Xbox Series X)', '- Xbox Series X')
    string = string.replace('xbox series x', 'Xbox Series X')
    string = string.replace('(Wii)', '- Wii')
    string = string.replace('(PC)', '- PC')
    string = string.replace('(PS4)', '- PS4')
    string = string.replace('(PS5)', '- PS5')
    string = string.replace('(Steelbook)', '- Steelbook Edition')
    string = string.replace('[Blu-ray]', '- Blu-ray')
    string = string.replace('[DVD]', '- DVD')
    string = string.replace('(Xbox 360)', '- Xbox 360')
    string = string.replace('(PlayStation 4)', '- PS4')
    string = string.replace('PlayStation 4 - PS4', '- PS4')
    string = string.replace('PlayStation 4', 'PS4 / PlayStation 4')
    string = string.replace('PlayStation 5 - PS5', '- PS5')
    string = string.replace('PlayStation 5', 'PS5 / PlayStation 5')
    string = string.replace('PS4', 'PS4 / PlayStation 4')
    string = string.replace('PlayStation 4  PlayStation 4', 'PlayStation 4')
    string = string.replace('PS5', 'PS5 / PlayStation 5')
    string = string.replace('PlayStation 5  PlayStation 5', 'PlayStation 5')
    string = string.replace('Game of the Year Edition', 'GOTY')
    return string


def split_string(string, args):
    for arg in args:
        m = 0
        k = 0
        while m != -1:
            i = string[k:].find(arg) + k
            k = i + 1
            if len(string)>i+1:
                while string[i+1] == ' ':
                    string = string[:i+1] + string[i+2:]
                    if len(string) <= i + 1:
                        break
            if i-1>=0:
                while string[i-1] == ' ':
                    string = string[:i-1] + string[i:]
                    i-=1
                    if i-1 <= 0:
                        break
            m = string[i+1:].find(arg)
    return string


def str_to_float(string):
    try:
        return float(string)
    except:
        return None


def str_to_int(string):
    try:
        return int(string)
    except:
        return None


def str_to_bool(string):
    try:
        if string=='0':
            return False
        elif string == '1':
            return True
        else:
            return None
    except:
        return None


def weight_to_float(string):
    string = string.replace('"', '')
    string = string.replace("'", "")
    string = string.replace(',', '.')
    string = string.replace(' ', '')
    string = string.replace('-', '00')
    string = string.replace('kg', '')
    string = string.replace('g', '')
    string = string.replace('mg', '')
    return string


def float_to_comma(floating_number):
    return str(floating_number).replace('.', ',')


def deumlaut(string):
    return string.replace(
        'ü', 'ue'
    ).replace(
        'ä', 'ae'
    ).replace(
        'ö', 'oe'
    ).replace(
        'Ü', 'Ue'
    ).replace(
        'Ä', 'Ae'
    ).replace(
        'Ö', 'Oe'
    )


def sign(a, b, comparator):
    try:
        if comparator == '=':
            return a==b
        elif comparator == '<':
            return a<b
        elif comparator == '<=':
            return a<=b
        elif comparator == '>':
            return a>b
        elif comparator == '>=':
            return a>=b
    except:
        return False


def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3


def marketplace_price_performance_measure(marketplace, selling_price, customer_shipping_price, own_shipping_price, buying_price, commission, tax):
    if marketplace == 'Idealo':
        try:
            end_price = selling_price + customer_shipping_price
            if commission * end_price > 12:
                a = 12
            else:
                a = commission * end_price
            if own_shipping_price > 3:
                b = own_shipping_price
            else:
                b = 3.55
            abs_margin = end_price / (1+tax/100) - buying_price - a - 0.0179 * end_price - 0.35 - b
            prc_margin = abs_margin / end_price
        except:
            abs_margin = None
            prc_margin = None
    elif marketplace == 'Ebay':
        try:
            end_price = selling_price+customer_shipping_price
            abs_margin = end_price/(1+tax/100) - buying_price - own_shipping_price - 0.35 - end_price*commission
            prc_margin = abs_margin/end_price
        except:
            abs_margin = None
            prc_margin = None
    elif marketplace == 'Lotus':
        try:
            end_price = selling_price+customer_shipping_price
            abs_margin = end_price/(1+tax/100) - buying_price - own_shipping_price - 0.35 - end_price*commission
            prc_margin = abs_margin/end_price
        except:
            abs_margin = None
            prc_margin = None
    else:
        prc_margin = None
        abs_margin = None
    return {'prc_margin': prc_margin, 'abs_margin': abs_margin}


def match_class(target):
    def do_match(tag):
        classes = tag.get('class', [])
        return all(c in classes for c in target)

    return do_match


iso_lang_dict = {'Abchasisch': 'ab',
                 'Afar': 'aa',
                 'Afrikaans': 'af',
                 'Akan': 'ak',
                 'Albanisch': 'sq',
                 'Amharisch': 'am',
                 'Arabisch': 'ar',
                 'Aragonesisch': 'an',
                 'Armenisch': 'hy',
                 'Assamesisch': 'as',
                 'Avarisch': 'av',
                 'Avestisch': 'ae',
                 'Aymara': 'ay',
                 'Aserbaidschanisch': 'az',
                 'Bambara': 'bm',
                 'Baschkirisch': 'ba',
                 'Baskisch': 'eu',
                 'Weißrussisch': 'be',
                 'Bengalisch': 'bn',
                 'Bihari': 'bh',
                 'Bislama': 'bi',
                 'Bosnisch': 'bs',
                 'Bretonisch': 'br',
                 'Bulgarisch': 'bg',
                 'Birmanisch': 'my',
                 'Katalanisch, Valencianisch': 'ca',
                 'Chamorro': 'ch',
                 'Tschetschenisch': 'ce',
                 'Chichewa': 'ny',
                 'Chinesisch': 'zh',
                 'Tschuwaschisch': 'cv',
                 'Kornisch': 'kw',
                 'Korsisch': 'co',
                 'Cree': 'cr',
                 'Kroatisch': 'hr',
                 'Tschechisch': 'cs',
                 'Dänisch': 'da',
                 'Dhivehi': 'dv',
                 'Niederländisch, Belgisches Niederländisch': 'nl',
                 'Belgisches Niederländisch': 'nl',
                 'Niederländisch': 'nl',
                 'Dzongkha': 'dz',
                 'Englisch': 'en',
                 'Esperanto': 'eo',
                 'Estnisch': 'et',
                 'Ewe': 'ee',
                 'Färöisch': 'fo',
                 'Fidschi': 'fj',
                 'Finnisch': 'fi',
                 'Französisch': 'fr',
                 'Fulfulde': 'ff',
                 'Galicisch, Galegisch': 'gl',
                 'Georgisch': 'ka',
                 'Deutsch': 'de',
                 'Griechisch': 'el',
                 'Guaraní': 'gn',
                 'Gujarati': 'gu',
                 'Haitianisch': 'ht',
                 'Hausa': 'ha',
                 'Hebräisch': 'he',
                 'Otjiherero': 'hz',
                 'Hindi': 'hi',
                 'Hiri Motu': 'ho',
                 'Ungarisch': 'hu',
                 'Interlingua': 'ia',
                 'Indonesisch': 'id',
                 'Interlingue': 'ie',
                 'Irisch': 'ga',
                 'Igbo': 'ig',
                 'Inupiaq': 'ik',
                 'Ido': 'io',
                 'Isländisch': 'is',
                 'Italienisch': 'it',
                 'Inuktitut': 'iu',
                 'Japanisch': 'ja',
                 'Javanisch': 'jv',
                 'Grönländisch, Kalaallisut': 'kl',
                 'Kannada': 'kn',
                 'Kanuri': 'kr',
                 'Kashmiri': 'ks',
                 'Kasachisch': 'kk',
                 'Khmer': 'km',
                 'Kikuyu': 'ki',
                 'Kinyarwanda, Ruandisch': 'rw',
                 'Kirgisisch': 'ky',
                 'Komi': 'kv',
                 'Kikongo': 'kg',
                 'Koreanisch': 'ko',
                 'Kurdisch': 'ku',
                 'oshiKwanyama': 'kj',
                 'Latein': 'la',
                 'Luxemburgisch': 'lb',
                 'Luganda': 'lg',
                 'Limburgisch, Südniederfränkisch': 'li',
                 'Lingála': 'ln',
                 'Laotisch': 'lo',
                 'Litauisch': 'lt',
                 'Kiluba': 'lu',
                 'Lettisch': 'lv',
                 'Manx,': 'gv',
                 'Manx-Gälisch': '',
                 'Mazedonisch': 'mk',
                 'Malagasy, Malagassi': 'mg',
                 'Malaiisch': 'ms',
                 'Malayalam': 'ml',
                 'Maltesisch': 'mt',
                 'Maori': 'mi',
                 'Marathi': 'mr',
                 'Marshallesisch': 'mh',
                 'Mongolisch': 'mn',
                 'Nauruisch': 'na',
                 'Navajo': 'nv',
                 'Nord-Ndebele': 'nd',
                 'Nepali': 'ne',
                 'Ndonga': 'ng',
                 'Bokmål': 'nb',
                 'Nynorsk': 'nn',
                 'Norwegisch': 'no',
                 'Yi': 'ii',
                 'Süd-Ndebele': 'nr',
                 'Okzitanisch': 'oc',
                 'Ojibwe': 'oj',
                 'Kirchenslawisch, Altkirchenslawisch': 'cu',
                 'Oromo': 'om',
                 'Oriya': 'or',
                 'Ossetisch': 'os',
                 'Panjabi, Pandschabi': 'pa',
                 'Pali': 'pi',
                 'Persisch': 'fa',
                 'Polnisch': 'pl',
                 'Paschtunisch': 'ps',
                 'Portugiesisch': 'pt',
                 'Quechua': 'qu',
                 'Bündnerromanisch, Romanisch': 'rm',
                 'Kirundi': 'rn',
                 'Rumänisch': 'ro',
                 'Russisch': 'ru',
                 'Sanskrit': 'sa',
                 'Sardisch': 'sc',
                 'Sindhi': 'sd',
                 'Nordsamisch': 'se',
                 '(Serbokroatisch)': '(sh)',
                 'Samoanisch': 'sm',
                 'Sango': 'sg',
                 'Serbisch': 'sr',
                 'Schottisch-gälisch': 'gd',
                 'Shona': 'sn',
                 'Singhalesisch': 'si',
                 'Slowakisch': 'sk',
                 'Slowenisch': 'sl',
                 'Somali': 'so',
                 'Sesotho, Süd-Sotho': 'st',
                 'Spanisch, Kastilisch': 'es',
                 'Spanisch': 'es',
                 'Kastilisch': 'es',
                 'Sundanesisch': 'su',
                 'Swahili': 'sw',
                 'Siswati': 'ss',
                 'Schwedisch': 'sv',
                 'Tamil': 'ta',
                 'Telugu': 'te',
                 'Tadschikisch': 'tg',
                 'Thai': 'th',
                 'Tigrinya': 'ti',
                 'Tibetisch': 'bo',
                 'Turkmenisch': 'tk',
                 'Tagalog': 'tl',
                 'Setswana': 'tn',
                 'Tongaisch': 'to',
                 'Türkisch': 'tr',
                 'Xitsonga': 'ts',
                 'Tatarisch': 'tt',
                 'Twi': 'tw',
                 'Tahitianisch, Tahitisch': 'ty',
                 'Uigurisch': 'ug',
                 'Ukrainisch': 'uk',
                 'Urdu': 'ur',
                 'Usbekisch': 'uz',
                 'Tshivenda': 've',
                 'Vietnamesisch': 'vi',
                 'Volapük': 'vo',
                 'Wallonisch': 'wa',
                 'Walisisch': 'cy',
                 'Wolof': 'wo',
                 'Westfriesisch': 'fy',
                 'isiXhosa': 'xh',
                 'Jiddisch': 'yi',
                 'Yoruba': 'yo',
                 'Zhuang': 'za',
                 'isiZulu': 'zu'}


def get_iso_lang_code(lang, ext_vals: bool = False):
    if ext_vals:
        if lang in ['Englisch', 'Französisch', 'Deutsch', 'Griechisch', 'Italienisch', 'Spanisch, Kastilisch', 'Spanisch']:
            return lang
        else:
            return iso_lang_dict[lang].upper()
    else:
        return iso_lang_dict[lang].upper()
