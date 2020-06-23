commercial_invoice_form = [
    {
        'question_text' : 'What is your business\'s name?',
        'key' : 'seller_name',
        'type' : 'text',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'What is your business\'s street address? (P.O. Box not accepted)',
        'key' : 'seller_address',
        'type' : 'text',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'What is your customer\'s business name?',
        'key' : 'buyer_name',
        'type' : 'text',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'What is your customer\'s street address? (P.O. Box not accepted)',
        'key' : 'buyer_address',
        'type' : 'text',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'What is the consignee\'s business name, if your customer is not the consignee?',
        'key' : 'consignee_name',
        'type' : 'text',
        'required' : False,
        'options' : ''
    },
    {
        'question_text' : 'What is your consignee\'s street address, if your customer is not the consignee? (P.O. Box not accepted)',
        'key' : 'consignee_address',
        'type' : 'text',
        'required' : False,
        'options' : ''
    },
    {
        'question_text' : 'What date of shipment should be indicated on the commercial invoice?',
        'key' : 'indicated_date_of_shipment',
        'type' : 'date',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'What is the country of export?',
        'key' : 'country_of_export',
        'type' : 'text',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'What is the country of origin for these goods?',
        'key' : 'country_of_origin',
        'type' : 'text',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'What incoterms should be shown on the commercial invoice?',
        'key' : 'incoterms_of_sale',
        'type' : 'checkbox',
        'required' : False,
        'options' : '["EXW", "FCA", "CPT", "CIP", "DAT", "DAP", "DDP", "FAS", "FOB", "CFR", "CIF"]'
    },
    {
        'question_text' : 'What currency is this purchase denominated in?',
        'key' : 'currency',
        'type' : 'text',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'Please describe the goods',
        'key' : 'goods_description',
        'type' : 'text',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'What reason for export should the document indicate? Skip for us to simply use \'Sale\'',
        'key' : 'reason_for_export',
        'type' : 'text',
        'required' : False,
        'options' : ''
    },
    {
        'question_text' : 'What is the unit of measure for this purchase? IE - barrels, pounds, logs, or service contract',
        'key' : 'unit_of_measure',
        'type' : 'text',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'How many units are you exporting?',
        'key' : 'units_purchased',
        'type' : 'decimal',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'What is the price per unit?',
        'key' : 'unit_price',
        'type' : 'decimal',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'What is the Harmonized Schedule code for this product?',
        'key' : 'hs_code',
        'type' : 'text',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'Do you have any additional comments you\'d like on the commercial invoice?',
        'key' : 'additional_comments',
        'type':'text',
        'required':False,
        'options':''
    },
    {
        'question_text' : 'Do you have any declarations for customs which you\'d like on the commercial invoice?',
        'key' : 'declaration_statement',
        'type':'text',
        'required':False,
        'options':''
    },
    {
        'question_text' : 'Type your name below to sign & affirm that you declare all the above answers to be true and correct',
        'key' : 'signature',
        'type':'text',
        'required':True,
        'options':''
    },
    {
        'question_text' : 'What is your title at the company issuing this commercial invoice?',
        'key' : 'signatory_title',
        'type':'text',
        'required':True,
        'options':''
    }
]

multimodal_bl_form = [
    {
        'question_text' : 'What is the carrier\'s business\'s name?',
        'key' : 'seller_name',
        'type' : 'text',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'What is the carrier\'s street address? (P.O. Box not accepted)',
        'key' : 'seller_address',
        'type' : 'text',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'What is the cosnignee\'s business name?',
        'key' : 'consignee_name',
        'type' : 'text',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'What is the consignee\'s street address? (P.O. Box not accepted)',
        'key' : 'consignee_address',
        'type' : 'text',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'If some party should be notified when the shipment arrives - for example, if your buyer is not the consignee and would like to be notified - what is that party\'s business name?',
        'key' : 'notifee_name',
        'type' : 'text',
        'required' : False,
        'options' : ''
    },
    {
        'question_text' : 'What is the notificatied party\'s street address? (P.O. Box not accepted)',
        'key' : 'notifee_address',
        'type' : 'text',
        'required' : False,
        'options' : ''
    },
    {
        'question_text' : 'What date of shipment should be indicated on the commercial invoice?',
        'key' : 'indicated_date_of_shipment',
        'type' : 'date',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'What is the vessel and voyage number the goods were shipped on, if applicable?',
        'key' : 'vessel_and_voyage',
        'type' : 'text',
        'required' : False,
        'options' : ''
    },
    {
        'question_text' : 'What is the place of dispatch for these goods?',
        'key' : 'place_of_dispatch',
        'type' : 'text',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'What is the port of loading for these goods, if applicable?',
        'key' : 'port_of_loading',
        'type' : 'text',
        'required' : False,
        'options' : ''
    },
    {
        'question_text' : 'What is the port of discharge for these goods, if applicable?',
        'key' : 'port_of_discharge',
        'type' : 'text',
        'required' : False,
        'options' : ''
    },
    {
        'question_text' : 'What is the final place of destination for these goods?',
        'key' : 'place_of_destination',
        'type' : 'text',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'Is this bill subject to charter party?',
        'key' : 'subject_to_charter_party',
        'type' : 'boolean',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'Please describe the goods',
        'key' : 'goods_description',
        'type' : 'text',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'What is the ID of the container the goods are being transported in?',
        'key' : 'container_id',
        'type' : 'text',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'Are the freight charges for these goods prepaid or collect?',
        'key' : 'freight_payment',
        'type' : 'radio',
        'required' : True,
        'options' : '["Prepaid", "Collect"]'
    },
    {
        'question_text' : 'What is the gross weight of the goods?',
        'key' : 'gross_weight',
        'type' : 'text',
        'required' : True,
        'options' : ''
    },
    {
        'question_text' : 'Type your name below to sign & affirm that you declare all the above answers to be true and correct',
        'key' : 'signature',
        'type':'text',
        'required':True,
        'options':''
    },
    {
        'question_text' : 'What is your title at the company issuing this multimodal bill of lading?',
        'key' : 'signatory_title',
        'type':'text',
        'required':True,
        'options':''
    }
]

import_permits = {

#dairy
('04') : ['Dairy','''
These products may be imported only byholders of permits from:

Department of Health and Human Services 
Food and Drug Administration 
Center for Food Safety and Applied Nutrition
Office of Food Labeling (HFS-156)
and the Department of Agriculture.''' ],

#fruits, vegetables, nuts
('07', '08', '14') : ['Fruits, Vegetables, Nuts' , '''an inspection certificate must be
issued by USDA’s Food Safety and Inspection Service to indicate import compliance.
Inquiries on general requirements should be made to USDA’s Agricultural Marketing
Service, Washington, DC 20250.'''],

#live animals
('01'): 
['Live Animals',
'''A permit for importation must be obtained from APHIS before shipping from the country
of origin.''' ],

#wildlife
('0106') : ['Wildlife', ''' Any commercial importer or exporter (there are some exceptions for exporters)
planning to import or export wildlife must first obtain a license from the Fish and
Wildlife Service. Applications and further information may be obtained from the Fish
and Wildlife Service, Assistant Regional Director for Law Enforcement, for the region in
which the importer or exporter is located. '''],


#insects
('0106.49.00') : ['Insects', ''''All packages containing live insects or their eggs, pupae, or larvae that
are not injurious to crops or trees are permitted entry into the United States
only if:
• They have a permit issued by the Animal and Plant Health Inspection
Service of the Department of Agriculture, and
• They are not prohibited by the U.S. Fish and Wildlife Service. '''],


# meat/poultry
('02') :
['Meat/Poultry' , 
''' All commercial shipments of meat and meat food products (derived from cattle, sheep,
swine, goats, and horses) offered for entry into the United States are subject to USDA
regulations and must be inspected by the Food Safety and Inspection Service (FSIS) of
that department and by CBP’s Agriculture Program and Liaison Office.
''']
,

#plant product
('06') : [
'Plant Products',  '''Import permits are required. Further information should be obtained from APHIS.'''],

#tobacco
('24') : [
'Tobacco',  ''' Importers of commercial quantities of
tobacco products must obtain an import permit from the Alcohol and
Tobacco Tax and Trade Bureau (TTB) of the Department of the
Treasury. '''],

#alcohol 
('22') : [
'Alcohol',  '''  distilled spirits, wines containing at least seven percent alcohol, or malt beverages
must first obtain an importer’s basic permit from the Alcohol and Tobacco Tax and Trade
Bureau (TTB) of the U.S. Treasury Department.  '''], 

#arms
('93') : [
'Arms Ammunition' , '''These items are
prohibited importations except when a license is issued by the Bureau of Alcohol,
Tobacco, Firearms and Explosives of the Department of Justice ''' ],

#food/food_products
('16', '17', '18', '19', '20', '21') : [
'Food Products',  ''' The BTA’s key elements require that manufacturers and shippers register the
facilities from which they export food and food products to the U.S. with the Food and
Drug Administration. Manufacturers and shippers must also provide the FDA with prior
notification (PN) for any food shipment covered by BTA regulations. '''],

# #bio TODO
# 'biological_drugs' : ''' Domestic as well as
# foreign manufacturers of such products must obtain a U.S. license for both the
# manufacturing establishment and for the product intended to be produced or imported.
# Additional information may be obtained from the Food and Drug Administration,  ''' ,

('6804.21.00') : 
['Rough Diamonds', ''' The importation of rough diamonds into the United States requires a Kimberley
Process Certificate and must be sealed in a tamper resistant container. '''],

# #fabrics
# 'textiles' : ''' Regulations and pamphlets containing the text of the Textile Fiber Products Identification
# Act may be obtained from the Federal Trade Commission, Washington, DC 20580. ''',

# 'wool' : ''' The provisions of the Wool Products Labeling Act apply to products
# manufactured in the United States as well as to imported products. Pamphlets containing
# the text of the Wool Products Labeling Act and regulations may be obtained from the
# Federal Trade Commission, Washington, DC 20580. ''',

# 'fur' : ''' Regulations and pamphlets
# containing the text of the Fur Products Labeling Act may be obtained from the Federal
# Trade Commission, Washington, DC 20580. ''',


#petroleum
('27') : [
'Petroleum' , ''' An import license
is no longer required, but an import authorization may be needed. These importations
may be subject to an oil-import license fee, which is collected and administered by the
Department of Energy. Inquiries should be directed to the Department of Energy ''' 
]
    }