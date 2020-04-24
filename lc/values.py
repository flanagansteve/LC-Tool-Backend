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
        'key' : 'buyer_name',
        'type' : 'text',
        'required' : False,
        'options' : ''
    },
    {
        'question_text' : 'What is your consignee\'s street address, if your customer is not the consignee? (P.O. Box not accepted)',
        'key' : 'buyer_address',
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
        'key' : 'units',
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
    }
]
