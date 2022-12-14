# TODO do we need to ask for shipment date? relevant for the default draft_presentation_date


default_questions = [
    {
        'question_text': 'Please fill out information about your business.',
        'key': 'applicant',
        'type': 'object',
        'required': False,
        'options': '',
        'section': 'Parties'
    },
    {
        'question_text': 'Name',
        'key': 'applicant.name',
        'type': 'text',
        'required': True,
        'options': '',
        'section': 'Parties'
    },
    {
        'question_text': 'Address',
        'key': 'applicant.address',
        'type': 'text',
        'required': True,
        'options': '',
        'section': 'Parties'
    },
    {
        'question_text': 'Country',
        'key': 'applicant.country',
        'type': 'text',
        'required': True,
        'options': '',
        'section': 'Parties'

    },
    {
        'question_text': 'Please fill out information about the beneficiary (IE, the other party to this transaction).',
        'key': 'beneficiary',
        'type': 'object',
        'required': False,
        'options': '',
        'section': 'Parties'
    },
    {
        'question_text': 'Name',
        'key': 'beneficiary.name',
        'type': 'text',
        'required': True,
        'options': '',
        'section': 'Parties'
    },
    {
        'question_text': 'Address',
        'key': 'beneficiary.address',
        'type': 'text',
        'required': True,
        'options': '',
        'section': 'Parties'
    },
    {
        'question_text': 'Country',
        'key': 'beneficiary.country',
        'type': 'text',
        'required': True,
        'options': '',
        'section': 'Parties'

    },
    {
        'question_text': 'Through what means will you forward the credit for this transaction, to either the beneficiary, your issuing bank, or a bank selected by your issuing bank?',
        'key': 'credit_delivery_means',
        'type': 'radio',
        'required': True,
        'options': '["S.W.I.F.T", "Courier", "Other"]',
        'section': 'Transaction Details'
    },
    {
        'question_text': 'You selected Other:',
        'key': 'credit_delivery_means_other',
        'type': 'text',
        'required': True,
        'options': '',
        'section': 'Transaction Details',
        'disabled': '{"key": "credit_delivery_means", "answer": [null, "S.W.I.F.T", "Courier"]}'
    },
    {
        'question_text': 'What is the total size of this purchase, in words?',
        'key': 'credit_amt_verbal',
        'type': 'text',
        'required': True,
        'options': '',
        'section': 'Transaction Details'
    },
    {
        'question_text': 'What is the total size of this purchase, in figures?',
        'key': 'credit_amt',
        'type': 'decimal',
        'required': True,
        'options': '',
        'section': 'Transaction Details'
    },
    {
        'question_text': 'What is the amount you are willing to cash secure?',
        'key': 'cash_secure',
        'type': 'decimal',
        'required': True,
        'options': '',
        'section': 'Transaction Details'
    },
    {
        'question_text': 'What currency is this purchase or credit denominated in?',
        'key': 'currency_denomination',
        'type': 'text',
        'required': True,
        'options': '',
        'section': 'Transaction Details'
    },
    {
        'question_text': 'Are you, the Applicant, requesting this Credit for account of an Account Party?',
        'key': 'account_party',
        'type': 'boolean',
        'required': True,
        'options': '',
        'section': 'Parties'
    },
    {
        'question_text': 'Are you and any Account Party jointly and severally obligated?',
        'key': 'applicant_and_ap_j_and_s_obligated',
        'type': 'boolean',
        'required': True,
        'options': '',
        'section': 'Parties',
        'disabled': '{"key": "account_party", "answer": [null, false]}'
    },
    {
        'question_text': 'What is the Account Party\'s name?',
        'key': 'account_party_name',
        'type': 'text',
        'required': True,
        'options': '',
        'section': 'Parties',
        'disabled': '{"key": "account_party", "answer": [null, false]}'
    },
    {
        'question_text': 'What is the Account Party\'s address?',
        'key': 'account_party_address',
        'type': 'text',
        'required': True,
        'options': '',
        'section': 'Parties',
        'disabled': '{"key": "account_party", "answer": [null, false]}'
    },
    {
        'question_text': 'Please fill out information about the Advising Bank (optional).',
        'key': 'advising_bank',
        'type': 'object',
        'required': False,
        'options': '',
        'section': 'Parties'
    },
    {
        'question_text': 'Name',
        'key': 'advising_bank.name',
        'type': 'text',
        'required': False,
        'options': '',
        'section': 'Parties'
    },
    {
        'question_text': 'Address',
        'key': 'advising_bank.address',
        'type': 'text',
        'required': True,
        'options': '',
        'section': 'Parties',
        'disabled': '{"key": "name", "answer": [null, ""]}'
    },
    {
        'question_text': 'Country',
        'key': 'advising_bank.country',
        'type': 'text',
        'required': True,
        'options': '',
        'section': 'Parties',
        'disabled': '{"key": "name", "answer": [null, ""]}'
    },
    {
        'question_text': 'Email Contact',
        'key': 'advising_bank.email',
        'type': 'text',
        'required': True,
        'options': '',
        'section': 'Parties',
        'disabled': '{"key": "name", "answer": [null, ""]}'
    },
    {
        'question_text': 'If you and your beneficiary established a Foreign Exchange Contract, what is the Foreign '
                         'Exchange Contract Number?',
        'key': 'forex_contract_num',
        'type': 'text',
        'required': False,
        'options': '',
        'section': 'Parties'
    },
    {
        'question_text': 'What percentage of currency exchange rate change will you tolerate?',
        'key': 'exchange_rate_tolerance',
        'type': 'decimal',
        'required': True,
        'options': '',
        'section': 'Parties',
        'disabled': '{"key": "forex_contract_num", "answer": ["*"]}'
    },
    {
        'question_text': 'What good or service are you purchasing?',
        'key': 'purchased_item',
        'type': 'hts',
        'required': True,
        'options': '',
        'section': 'Goods Details'
    },
    {
        'question_text': 'What is the HTS code of the good or service?',
        'key': 'hts_code',
        'type': 'text',
        'required': True,
        'options': '',
        'section': 'Goods Details'
    },
    {
        'question_text': 'What is the unit of measure of your purchase?',
        'key': 'unit_of_measure',
        'type': 'dropdown',
        'required': True,
        'options': '["No unit of measure", "square meters", "thousands of kilowatt-hours", "meters", "number of '
                   'items", "number of pairs", "liters", "kilograms", "thousands of items", "packages", '
                   '"dozen of items", "cubic meters", "carats"]',
        'initial_value': 'kilograms',
        'section': 'Goods Details'
    },
    {
        'question_text': 'How many units are you purchasing?',
        'key': 'units_purchased',
        'type': 'decimal',
        'required': True,
        'options': '',
        'section': 'Goods Details'
    },
    {
        'question_text': 'What percentage of error in the received units will you tolerate?',
        'key': 'unit_error_tolerance',
        'type': 'decimal',
        'required': True,
        'options': '',
        'section': 'Goods Details'
    },
    {
        'question_text': 'How would you like the payout of this transaction to be confirmed?',
        'key': 'confirmation_means',
        'type': 'radio',
        'required': True,
        'options': '["No Confirmation", "Confirmation by a bank selected by the beneficiary", "Confirmation by a bank '
                   'selected by SVB in the beneficiary\'s country"]',
        'section': 'Individual Party Responsibilities'
    },
    {
        'question_text': 'All of the issuing bank\'s charges will be paid by you, the Applicant. Who should pay '
                         'charges from other banks party to this transaction?',
        'key': 'paying_other_banks_fees',
        'type': 'radio',
        'required': True,
        'options': '["You, the applicant", "The beneficiary"]',
        'section': 'Individual Party Responsibilities'
    },
    {
        'question_text': 'Where should the Credit expire - or in other words, where must the documentary requirements '
                         'be presented prior to the credit\'s expiration date?',
        'key': 'credit_expiry_location',
        'type': 'radio',
        'required': True,
        'options': '["Confirming bank\'s office", "Issuing bank\'s office"]',
        'section': 'Individual Party Responsibilities'
    },
    {
        'question_text': 'When should this credit expire?',
        'key': 'expiration_date',
        'type': 'date',
        'required': True,
        'options': '',
        'section': 'Individual Party Responsibilities'
    },
    {
        'question_text': 'When should drafts be presented? If not specified, we will default to 21 days after the '
                         'date of shipment. This date must be prior to expiration of the LC.',
        'key': 'draft_presentation_date',
        'type': 'date_ship',
        'required': False,
        'options': '',
        'section': 'Individual Party Responsibilities'
    },
    {
        'question_text': 'What percentage of invoice value should Drafts include? We will use 100% if not otherwise '
                         'specified',
        'key': 'drafts_invoice_value',
        'type': 'decimal',
        'required': False,
        'options': '',
        'initial_value': 100,
        'section': 'Individual Party Responsibilities'
    },
    {
        'question_text': 'How would you like to make Credit available? Standard options include payment at sight, '
                         'acceptance some number of days after sight, acceptance some number of days after the agreed '
                         'shipment date, acceptance some number of days after the agreed invoice date, and acceptance '
                         'some number of days after the agreed draft date. Feel free to specify some other '
                         'alternative.',
        'key': 'credit_availability',
        'type': 'pay',
        'required': True,
        'options': '',
        'section': 'Individual Party Responsibilities'
    },
    {
        'question_text': 'Credit will be made availabe acceptance some number of days after:',
        'key': 'credit_availability_days_after',
        'type': 'radio',
        'required': True,
        'options': '["sight", "the agreed shipment date", "the agreed invoice date", "the agreed draft date"]',
        'section': 'Individual Party Responsibilities',
        'disabled': '{"key": "credit_availability", "answer": [null, false]}'
    },
    {
        'question_text': 'Please state the number of days after',
        'key': 'credit_availability_days',
        'type': 'decimal',
        'required': True,
        'options': '',
        'section': 'Individual Party Responsibilities',
        'disabled': '{"key": "credit_availability", "answer": [null, false]}'
    },
    {
        'question_text': 'Who are acceptance and discount charges for the account of?',
        'key': 'paying_acceptance_and_discount_charges',
        'type': 'radio',
        'required': True,
        'options': '["You, the applicant", "The beneficiary"]',
        'section': 'Individual Party Responsibilities'
    },
    {
        'question_text': 'When may Deferred payment take place (the maturity date of the deferred payment obligation)?',
        'key': 'deferred_payment_date',
        'type': 'date',
        'required': True,
        'options': '',
        'section': 'Individual Party Responsibilities'
    },
    {
        'question_text': 'What bank(s) do you authorise to negotiate deferred payment?',
        'key': 'delegated_negotiating_banks',
        'type': 'text',
        'required': True,
        'options': '',
        'section': 'Individual Party Responsibilities'
    },
    {
        'question_text': 'Would you permit partial shipment?',
        'key': 'partial_shipment_allowed',
        'type': 'boolean',
        'required': True,
        'options': '',
        'section': 'Logistical Details'
    },
    {
        'question_text': 'Would you permit partial transshipment?',
        'key': 'transshipment_allowed',
        'type': 'boolean',
        'required': True,
        'options': '',
        'section': 'Logistical Details'
    },
    {
        'question_text': 'Where should merchandise be shipped or dispatched from/taken in charge at?',
        'key': 'merch_charge_location',
        'type': 'text',
        'required': True,
        'options': '',
        'section': 'Logistical Details'
    },
    {
        'question_text': 'If applicable, what is the latest date merchandise should be taken charge of?',
        'key': 'late_charge_date',
        'type': 'date',
        'required': False,
        'options': '',
        'section': 'Logistical Details'
    },
    {
        'question_text': 'Where will merchandise be transported to, once taken charge of?',
        'key': 'charge_transportation_location',
        'type': 'text',
        'required': True,
        'options': '',
        'section': 'Logistical Details'
    },
    {
        'question_text': 'For terms of shipment, what mode of transport, if any, should be shown on the Commercial '
                         'Invoice?',
        'key': 'incoterms_to_show',
        'type': 'checkbox',
        'required': False,
        'options': '["EXW", "FCA", "CPT", "CIP", "DAT", "DAP", "DDP", "FAS", "FOB", "CFR", "CIF"]',
        'section': 'Logistical Details'
    },
    {
        'question_text': 'What is the named place of destination?',
        'key': 'named_place_of_destination',
        'type': 'text',
        'required': True,
        'options': '',
        'section': 'Logistical Details'
    },
    {
        'question_text': 'Will you, the Applicant, arrange your own insurance? If not, you should request evidence of '
                         'insurance from the Beneficiary as documents to accompany the Drafts.',
        'key': 'arranging_own_insurance',
        'type': 'boolean',
        'required': True,
        'options': '',
        'section': 'Document Requirements'
    },
    {
        'question_text': 'Assuming your beneficiary arranges the insurance on this purchase, what percentage of the '
                         'invoice value would you like to have insured by a Negotiable Insurance Policy or '
                         'Certificate? Specify 0% or skip if this is unnecessary for this transaction. 110% is '
                         'standard.',
        'key': 'insurance_percentage',
        'type': 'decimal',
        'required': False,
        'options': '',
        'section': 'Document Requirements',
        'disabled': '{"key": "arranging_own_insurance", "answer": [true]}'
    },
    {
        'question_text': 'Assuming your beneficiary arranges the insurance on this purchase, what risks should it '
                         'cover?',
        'key': 'selected_insurance_risks_covered',
        'type': 'checkbox',
        'required': False,
        'options': '["Marine Risk", "Air Risk", "War Risk", "Theft/Pilferage/Non-Delivery Risks", "All Risks"]',
        'section': 'Document Requirements',
        'disabled': '{"key": "arranging_own_insurance", "answer": [true]}'
    },
    {
        'question_text': 'Assuming your beneficiary arranges the insurance on this purchase, are there any other '
                         'risks you\'d like covered, not listed in the previous question?',
        'key': 'other_insurance_risks_covered',
        'type': 'text',
        'required': False,
        'options': '',
        'section': 'Document Requirements',
        'disabled': '{"key": "arranging_own_insurance", "answer": [true]}'
    },
    {
        'question_text': 'Please fill out the document requirements for the Signed Commercial Invoice.',
        'key': 'commercial_invoice',
        'type': 'object',
        'required': False,
        'options': '',
        'section': 'Document Requirements'
    },
    {
        'question_text': 'Name',
        'key': 'commercial_invoice.name',
        'type': 'text',
        'required': False,
        'options': '',
        'section': '',
        'initial_value': 'Signed Commercial Invoice',
        'disabled': True
    },
    {
        'question_text': 'Include Original',
        'key': 'commercial_invoice.original',
        'type': 'boolean',
        'required': True,
        'options': '',
        'section': ''
    },
    {
        'question_text': 'Copies',
        'key': 'commercial_invoice.copies',
        'type': 'number',
        'required': True,
        'options': '',
        'section': ''
    },
    {
        'question_text': 'What, if any, Transport Documents should accompany '
                         'the Drafts?',
        'key': 'required_transport_docs',
        'type': 'array_of_objs',
        'required': False,
        'options': '["Full set original clean on board Marine Bills of '
                   'Lading or multimodal or combined transport Bill of '
                   'Lading issued to order of shipper, endorsed in blank", '
                   '"Clean Air Waybill consigned to the \'Applicant\'", '
                   '"Clean Truck / Rail Bill of Lading consigned to the '
                   '\'Applicant\'"]',
        'section': 'Document Requirements',
        'settings': '{"name":"Transport Document"}'
    },
    {
        'question_text': 'Name',
        'key': 'required_transport_docs.name',
        'type': 'radio',
        'required': True,
        'options': '',
        'section': '',
    },
    {
        'question_text': 'Required Values',
        'key': 'required_transport_docs.required_values',
        'type': 'radio',
        'required': True,
        'options': '["Freight Collect", "Freight Prepaid"]',
        'section': ''
    },
    {
        'question_text': 'Please fill out the document requirements for the Packing List.',
        'key': 'packing_list',
        'type': 'object',
        'required': False,
        'options': '',
        'section': 'Document Requirements'
    },
    {
        'question_text': 'Name',
        'key': 'packing_list.name',
        'type': 'text',
        'required': False,
        'options': '',
        'section': '',
        'initial_value': 'Packing List',
        'disabled': True
    },
    {
        'question_text': 'Copies',
        'key': 'packing_list.copies',
        'type': 'number',
        'required': True,
        'options': '',
        'section': ''
    },
    {
        'question_text': 'Please fill out the document requirements for the Certificate of Origin.',
        'key': 'certificate_of_origin',
        'type': 'object',
        'required': False,
        'options': '',
        'section': 'Document Requirements'
    },
    {
        'question_text': 'Name',
        'key': 'certificate_of_origin.name',
        'type': 'text',
        'required': False,
        'options': '',
        'section': '',
        'initial_value': 'Certificate of Origin',
        'disabled': True
    },
    {
        'question_text': 'Copies',
        'key': 'certificate_of_origin.copies',
        'type': 'number',
        'required': True,
        'options': '',
        'section': ''
    },
    {
        'question_text': 'Please fill out the document requirements for the Inspection Certificate.',
        'key': 'inspection_certificate',
        'type': 'object',
        'required': False,
        'options': '',
        'section': 'Document Requirements'
    },
    {
        'question_text': 'Name',
        'key': 'inspection_certificate.name',
        'type': 'text',
        'required': False,
        'options': '',
        'section': '',
        'initial_value': 'Inspection Certificate',
        'disabled': True
    },
    {
        'question_text': 'Copies',
        'key': 'inspection_certificate.copies',
        'type': 'number',
        'required': True,
        'options': '',
        'section': ''
    },
    {
        'question_text': 'Are there any other documents which you\'d like the Drafts to be accompanied with?',
        'key': 'other_draft_accompiants',
        'type': 'array_of_objs',
        'required': False,
        'options': '',
        'section': 'Document Requirements',
        'settings': '{"name":"Documentary Requirement"}'
    },
    {
        'question_text': 'Name',
        'key': 'other_draft_accompiants.name',
        'type': 'text',
        'required': True,
        'options': '',
        'section': ''
    },
    {
        'question_text': 'Due Date',
        'key': 'other_draft_accompiants.due_date',
        'type': 'date',
        'required': True,
        'options': '',
        'section': ''
    },
    {
        'question_text': 'Required Values',
        'key': 'other_draft_accompiants.required_values',
        'type': 'text',
        'required': True,
        'options': '',
        'section': ''
    },
    {
        'question_text': 'Who should be notified when Drafts and accompanying documents are received? We will notify '
                         'the Applicant unless otherwise specified.',
        'key': 'doc_reception_notifees',
        'type': 'text',
        'required': False,
        'options': '',
        'section': 'Document Requirements'
    },
    {
        'question_text': 'Are there any other instructions you\'d like to include?',
        'key': 'other_instructions',
        'type': 'text',
        'required': False,
        'options': '',
        'section': 'Final'
    },
    {
        'question_text': 'Please describe the merchandise',
        'key': 'merch_description',
        'type': 'text',
        'required': True,
        'options': '',
        'section': 'Goods Details'
    },
    {
        'question_text': 'Should this Credit be transferable, and if so, to whose account should transfer charges be?',
        'key': 'transferability',
        'type': 'radio',
        'required': True,
        'options': '["Transferable, fees charged to the applicant\'s account", "Transferable, fees charged to the '
                   'beneficiary\'s account", "Non-transferable"]',
        'section': 'Final'
    }
]
