# -*- coding: utf-8 -*-

"""Some system-variables and -dictionaries to look up."""

image_server = 'https://strikeusifucan.com/'

spec_trait_2_dict = {1: ['Commodore 64',
                         'PSV / PlayStation Vita', 'PS2 / PlayStation 2', 'PS3 / PlayStation 3', 'PS4 / PlayStation 4', 'PS5 / PlayStation 5',
                         'Nintendo Classic Mini NES', 'NES', 'SNES', 'Nintendo DS', 'Nintendo 2DS', 'Nintendo 3DS', 'Nintendo 3DS XL', 'Nintendo New 3DS', 'Nintendo New 3DS XL', 'Wii', 'Wii U',
                         'Nintendo Switch',
                         'Xbox 360', 'Xbox ONE', 'Xbox Series X|S', 'Xbox Series X',
                         'PC', 'Android']}

spec_trait_3_dict = {1: ['USK', 'AT', 'EU', 'AUS', 'UK', 'Nordic', 'PEGI']}

version_normalizer_dict = {'AT': 'EU Version', 'UK': 'EU Version', 'Nordic': 'EU Version', 'PEGI': 'EU Version', 'EU': 'EU Version', 'USK': 'Deutsche Version'}

comma_split_features = ['language_in_game', 'language_on_cover', 'language_subtitles', 'genre']

region_dict = {'German': 'USK', 'English': 'UK', 'Nordic': 'Nordic', 'Finnish': 'Nordic', 'Danish': 'Nordic', 'Norwegian': 'Nordic', 'Swedish': 'Nordic', 'French': 'EU', 'Italian': 'EU',
               'Import': 'PEGI', '': ''}

platform_dict = {'Commodore 64': 'Commodore 64',
                 'PlayStation': 'PS / PlayStation',
                 'PS / PlayStation': 'PS / PlayStation',
                 'PS Vita': 'PSV / PlayStation Vita',
                 'PSV / PlayStation Vita': 'PSV / PlayStation Vita',
                 'PlayStation Vita': 'PSV / PlayStation Vita',
                 'PlayStation 2': 'PS2 / PlayStation 2',
                 'PS2 / PlayStation 2': 'PS2 / PlayStation 2',
                 'PS2': 'PS2 / PlayStation 2',
                 'PlayStation 3 (PS3)': 'PS3 / PlayStation 3',
                 'PlayStation 3': 'PS3 / PlayStation 3',
                 'PS3 / PlayStation 3': 'PS3 / PlayStation 3',
                 'PS3': 'PS3 / PlayStation 3',
                 'PS4': 'PS4 / PlayStation 4',
                 'Playstation 4 (PS4)': 'PS4 / PlayStation 4',
                 'PlayStation 4 (PS4)': 'PS4 / PlayStation 4',
                 'PlayStation 4': 'PS4 / PlayStation 4',
                 'PS4 / PlayStation 4': 'PS4 / PlayStation 4',
                 'PlayStation 5 (PS5)': 'PS5 / PlayStation 5',
                 'PlayStation 5': 'PS5 / PlayStation 5',
                 'PS5 / PlayStation 5': 'PS5 / PlayStation 5',
                 'PS5': 'PS5 / PlayStation 5',
                 'Nintendo Classic Mini NES': 'Nintendo Classic Mini NES',
                 'NES': 'NES',
                 'Nintendo Entertainment System': 'NES',
                 'Super Nintendo': 'SNES',
                 'SNES': 'SNES',
                 'N64': 'N64',
                 'GC': 'Gamecube',
                 'Gamecube': 'Gamecube',
                 'Nintendo DS': 'Nintendo DS',
                 'DS': 'Nintendo DS',
                 'Nintendo 2DS': 'Nintendo 2DS',
                 'Nintendo 3DS': 'Nintendo 3DS',
                 '3DS': 'Nintendo 3DS',
                 'Nintendo 3DS XL': 'Nintendo 3DS XL',
                 'Nintendo New 3DS': 'Nintendo New 3DS',
                 'Nintendo New 3DS XL': 'Nintendo New 3DS XL',
                 'Wii': 'Wii',
                 'Wii U': 'Wii U',
                 'WiiU': 'Wii U',
                 'Nintendo Switch': 'Nintendo Switch',
                 'SWITCH': 'Nintendo Switch',
                 'Xbox 360': 'Xbox 360',
                 'XBox 360': 'Xbox 360',
                 'Xbox One': 'Xbox ONE',
                 'Xbox ONE': 'Xbox ONE',
                 'XB-ONE': 'Xbox ONE',
                 'XONE': 'Xbox ONE',
                 'XONE/X360': 'Xbox ONE',
                 'Xbox One S': 'Xbox ONE',
                 'Xbox Series': 'Xbox Series X|S',
                 'Xbox Series X': 'Xbox Series X',
                 'Xbox Series X|S': 'Xbox Series X|S',
                 'XBOX Series X': 'Xbox Series X',
                 'XSX/XONE': 'Xbox Series X',
                 'XSX': 'Xbox Series X',
                 'Windows': 'PC',
                 'Microsoft': 'PC',
                 'PC': 'PC',
                 'Android': 'Android',
                 'Handy': 'Handy',
                 '': '',
                 'Multiplattform': '',
                 'Merchandise': '',
                 'Code-Card': '',
                 'Spielzeug': ''}

ebay_ff_policy_ids = {'DE_DeutschePostBrief & DE_SonstigeInternational - 0 DAYS': '207649563015',
                      'DE_DeutschePostBrief & DE_SonstigeInternational - 1 DAYS': '207666723015',
                      'DE_DeutschePostBrief & DE_SonstigeInternational - 2 DAYS': '207666727015',
                      'DE_DeutschePostBrief & DE_SonstigeInternational - 3 DAYS': '207666731015',
                      'DE_DeutschePostBrief & DE_SonstigeInternational - 4 DAYS': '207666740015',
                      'DE_DeutschePostBrief & DE_SonstigeInternational - 5 DAYS': '207667213015',
                      'DE_DeutschePostBrief & DE_SonstigeInternational - 6 DAYS': '207666745015',
                      'DE_DeutschePostBrief & DE_SonstigeInternational - 7 DAYS': '207666747015',
                      'DE_DeutschePostBrief & DE_SonstigeInternational - 10 DAYS': '207666754015',
                      'DE_DeutschePostBrief & DE_SonstigeInternational - 15 DAYS': '207666758015',
                      'DE_DeutschePostBrief & DE_SonstigeInternational - 20 DAYS': '207666761015',
                      'DE_DeutschePostBrief & DE_SonstigeInternational - 30 DAYS': '207666767015',
                      'DE_DeutschePostBrief & DE_SonstigeInternational - 40 DAYS': '207666770015',
                      'DE_DHLPaket & DE_SonstigeInternational - 0 DAYS': '207649743015',
                      'DE_DHLPaket & DE_SonstigeInternational - 1 DAYS': '207666655015',
                      'DE_DHLPaket & DE_SonstigeInternational - 2 DAYS': '207666657015',
                      'DE_DHLPaket & DE_SonstigeInternational - 3 DAYS': '207666661015',
                      'DE_DHLPaket & DE_SonstigeInternational - 4 DAYS': '207666662015',
                      'DE_DHLPaket & DE_SonstigeInternational - 5 DAYS': '207666666015',
                      'DE_DHLPaket & DE_SonstigeInternational - 6 DAYS': '207666668015',
                      'DE_DHLPaket & DE_SonstigeInternational - 7 DAYS': '207666670015',
                      'DE_DHLPaket & DE_SonstigeInternational - 10 DAYS': '207666674015',
                      'DE_DHLPaket & DE_SonstigeInternational - 15 DAYS': '207666676015',
                      'DE_DHLPaket & DE_SonstigeInternational - 20 DAYS': '207666677015',
                      'DE_DHLPaket & DE_SonstigeInternational - 30 DAYS': '207666678015',
                      'DE_DHLPaket & DE_SonstigeInternational - 40 DAYS': '207666679015',
                      'DE_DHLAlterssichtprüfung18 & DE_SonstigeInternational - 0 DAYS': '207649564015',
                      'DE_DHLAlterssichtprüfung18 & DE_SonstigeInternational - 1 DAYS': '207666724015',
                      'DE_DHLAlterssichtprüfung18 & DE_SonstigeInternational - 2 DAYS': '207666729015',
                      'DE_DHLAlterssichtprüfung18 & DE_SonstigeInternational - 3 DAYS': '207666736015',
                      'DE_DHLAlterssichtprüfung18 & DE_SonstigeInternational - 4 DAYS': '207666741015',
                      'DE_DHLAlterssichtprüfung18 & DE_SonstigeInternational - 5 DAYS': '207666743015',
                      'DE_DHLAlterssichtprüfung18 & DE_SonstigeInternational - 6 DAYS': '207666746015',
                      'DE_DHLAlterssichtprüfung18 & DE_SonstigeInternational - 7 DAYS': '207666751015',
                      'DE_DHLAlterssichtprüfung18 & DE_SonstigeInternational - 10 DAYS': '207666756015',
                      'DE_DHLAlterssichtprüfung18 & DE_SonstigeInternational - 15 DAYS': '207666759015',
                      'DE_DHLAlterssichtprüfung18 & DE_SonstigeInternational - 20 DAYS': '207666764015',
                      'DE_DHLAlterssichtprüfung18 & DE_SonstigeInternational - 30 DAYS': '207667221015',
                      'DE_DHLAlterssichtprüfung18 & DE_SonstigeInternational - 40 DAYS': '207667223015',
                      'DE_DeutschePostBrief - 0 DAYS': '210102411015',
                      'DE_DeutschePostBrief - 1 DAYS': '210102412015',
                      'DE_DeutschePostBrief - 2 DAYS': '210102413015',
                      'DE_DeutschePostBrief - 3 DAYS': '210102414015',
                      'DE_DeutschePostBrief - 4 DAYS': '210102415015',
                      'DE_DeutschePostBrief - 5 DAYS': '210102416015',
                      'DE_DeutschePostBrief - 6 DAYS': '210102417015',
                      'DE_DeutschePostBrief - 7 DAYS': '210102420015',
                      'DE_DeutschePostBrief - 10 DAYS': '210102423015',
                      'DE_DeutschePostBrief - 15 DAYS': '210102424015',
                      'DE_DeutschePostBrief - 20 DAYS': '210102425015',
                      'DE_DeutschePostBrief - 30 DAYS': '210102426015',
                      'DE_DeutschePostBrief - 40 DAYS': '210102427015',
                      'DE_DHLPaket - 0 DAYS': '210102428015',
                      'DE_DHLPaket - 1 DAYS': '210102429015',
                      'DE_DHLPaket - 2 DAYS': '210102430015',
                      'DE_DHLPaket - 3 DAYS': '210102431015',
                      'DE_DHLPaket - 4 DAYS': '210102432015',
                      'DE_DHLPaket - 5 DAYS': '210102434015',
                      'DE_DHLPaket - 6 DAYS': '210102435015',
                      'DE_DHLPaket - 7 DAYS': '210102436015',
                      'DE_DHLPaket - 10 DAYS': '210102438015',
                      'DE_DHLPaket - 15 DAYS': '210102439015',
                      'DE_DHLPaket - 20 DAYS': '210102440015',
                      'DE_DHLPaket - 30 DAYS': '210102442015',
                      'DE_DHLPaket - 40 DAYS': '210102444015',
                      'DE_DHLAlterssichtprüfung18 - 0 DAYS': '210102445015',
                      'DE_DHLAlterssichtprüfung18 - 1 DAYS': '210102446015',
                      'DE_DHLAlterssichtprüfung18 - 2 DAYS': '210102447015',
                      'DE_DHLAlterssichtprüfung18 - 3 DAYS': '210102448015',
                      'DE_DHLAlterssichtprüfung18 - 4 DAYS': '210102449015',
                      'DE_DHLAlterssichtprüfung18 - 5 DAYS': '210102450015',
                      'DE_DHLAlterssichtprüfung18 - 6 DAYS': '210102451015',
                      'DE_DHLAlterssichtprüfung18 - 7 DAYS': '210102452015',
                      'DE_DHLAlterssichtprüfung18 - 10 DAYS': '210102454015',
                      'DE_DHLAlterssichtprüfung18 - 15 DAYS': '210102455015',
                      'DE_DHLAlterssichtprüfung18 - 20 DAYS': '210102456015',
                      'DE_DHLAlterssichtprüfung18 - 30 DAYS': '210102458015',
                      'DE_DHLAlterssichtprüfung18 - 40 DAYS': '210102459015'}
#DE_DeutschePostBrief & DE_SonstigeInternational - 0 DAYS
#DP 5 DAYS
#DHL_ALT 30 DAYS
#DHL_ALT 40 DAYS

basic_return_policy = '''Informationen zur außergerichtlichen Beilegung von verbraucherrechtlichen Streitigkeiten:

Zur außergerichtlichen Beilegung von verbraucherrechtlichen Streitigkeiten hat die Europäische Union eine Online-Plattform (“OS-Plattform”) eingerichtet.
Die Plattform finden Sie unter https://ec.europa.eu/consumers/odr/ 
Unsere Mail-Adresse lautet: service@lotusicafe.de


Widerrufsbelehrung

Widerrufsrecht für Verbraucher

Sie haben das Recht, binnen 1 Monat ohne Angabe von Gründen diesen Vertrag zu widerrufen.

Die Widerrufsfrist beträgt 1 Monat ab dem Tag, 

 a) an dem Sie oder ein von Ihnen benannter Dritter, der nicht der Beförderer ist, die Waren 
     in Besitz genommen haben bzw. hat;
 b) an dem Sie oder ein von Ihnen benannter Dritter, der nicht der Beförderer ist, die letzte 
                Ware in Besitz genommen haben bzw. hat, sofern Sie mehrere Waren im Rahmen einer 
     einheitlichen Bestellung bestellt haben und die getrennt geliefert werden.

Um Ihr Widerrufsrecht auszuüben müssen Sie uns

Faruk Önal - lotusicafe
Proskauer Straße 32
10247 Berlin

Tel-Nr.: 030/35306768 
Email: service@lotusicafe.de

mittels einer eindeutigen Erklärung (z.B. ein mit der Post versandter Brief, Fax oder Email) über Ihren Entschluss, diesen Vertrag zu widerrufen, informieren. Sie können dafür das beigefügte Muster-Widerrufsformular verwenden, das jedoch nicht vorgeschrieben ist.

Zur Wahrung der Widerrufsfrist reicht es aus,  dass Sie die Mitteilung über die Ausübung des Widerrufsrechts vor Ablauf der Widerrufsfrist absenden.

Folgen des Widerrufs

Wenn Sie diesen Vertrag widerrufen, haben wir Ihnen alle Zahlungen, die wir von Ihnen erhalten haben, einschließlich der Lieferkosten (mit Ausnahme der zusätzlichen Kosten, die sich daraus ergeben, dass Sie eine andere Art der Lieferung als die von uns angebotene, günstigste Standartlieferung gewählt haben) unverzüglich und spätestens binnen 14 Tagen ab dem Tag zurückzuzahlen, an dem die Mitteilung über Ihren Widerruf dieses Vertrags bei uns eingegangen ist. Für diese Rückzahlung verwenden wir dasselbe Zahlungsmittel, das Sie bei der ursprünglichen Transaktion eingesetzt haben, es sei denn, mit Ihnen wurde ausdrücklich etwas anderes vereinbart; in keinem Fall werden Ihnen wegen dieser Rückzahlung Entgelte berechnet. Wir können die Rückzahlung verweigern, bis wir die Waren wieder zurückerhalten haben oder bis Sie den Nachweis erbracht haben, dass Sie die Waren zurückgesandt haben, je nachdem, welches der frühere Zeitpunkt ist.

Sie haben die Waren unverzüglich, in jedem Fall spätestens binnen 14 Tagen ab dem Tag, an dem Sie uns über den Widerruf dieses Vertrags unterrichten, an uns, Faruk Önal – lotusicafe, Proskauer Straße 32,10247 Berlin, zurückzusenden oder zu übergeben. Die Frist ist gewahrt, wenn sie die Waren vor Ablauf der Frist von vierzehn Tagen absenden.

Sie tragen die unmittelbaren Kosten der Rücksendung der Waren.

Sie müssen für einen etwaigen Wertverlust der Waren nur aufkommen, wenn dieser Wertverlust auf einem zur Prüfung der Beschaffenheit, Eigenschaften und Funktionsweise der Waren nicht notwendigen Umgang mit ihnen zurückzuführen ist.

Vorzeitiges Erlöschen des Widerrufsrechts
Das Widerrufsrecht erlischt vorzeitig bei Verträgen zur Lieferung von Ton- oder Videoaufnahmen oder Computersoftware in einer versiegelten Packung, wenn die Versiegelung nach der Lieferung entfernt wurde. 

Das Widerrufsrecht erlischt vorzeitig bei Verträgen zur Lieferung versiegelter Waren, die aus Gründen des Gesundheitsschutzes oder der Hygiene nicht zur Rückgabe geeignet sind, wenn ihre Versiegelung nach der Lieferung entfernt wurde.

Widerrufsformular

Wenn Sie den Vertrag widerrufen wollen, dann füllen Sie bitte dieses Formular aus und senden es zurück an:

Faruk Önal - lotusicafe
Proskauer Straße 32
10247 Berlin
Email: service@lotusicafe.de

Hiermit widerrufe(n) ich/wir (*) den von mir/uns (*) abgeschlossenen Vertrag über den Kauf der folgenden Ware(n):

…......................................................................................................................................................

…......................................................................................................................................................

Bestellt am.................................(*)   erhalten am....................................(*)

…...............................................................................................................
Name des/der Verbraucher(s)

…...............................................................................................................
Anschrift des/der Verbraucher(s)


…....................................................
Unterschrift des/der Verbraucher(s)
(nur bei Übermittlung in Papierform erforderlich)

…..............................
Datum

_______________________________________________________
(*) Unzutreffendes bitte streichen'''

holidays = [
    '2022-01-01',
    '2022-04-15',
    '2022-04-18',
    '2022-05-01',
    '2022-05-26',
    '2022-06-06',
    '2022-10-03',
    '2022-12-25',
    '2022-12-26',
    '2023-01-01',
    '2023-04-07',
    '2023-04-10',
    '2023-05-01',
    '2023-05-18',
    '2023-05-29',
    '2023-10-03',
    '2023-12-25',
    '2023-12-26',
    '2024-01-01',
    '2024-03-29',
    '2024-04-01',
    '2024-05-01',
    '2024-05-09',
    '2024-05-20',
    '2024-10-03',
    '2024-12-25',
    '2024-12-26'
]
