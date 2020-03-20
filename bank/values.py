# TODO do we need to ask for shipment date? relevant for the default
#      draft_presentation_date
# TODO how to represent multiple choice? Relevant for
# - confirmation_means
# - paying_other_banks_fees
# - credit_expiry_location
# - credit_availability [kind of]
# - paying_acceptance_and_discount_charges
# - possibly, delegated_negotiating_banks
# - incoterms_to_show
# - draft_accompiant_invoice
# - draft_accompiant_transport_docs
# - transport_doc_marking
# - insurance_risks_covered
# - transferability
# 1. could just do it as text, and only 'act' on the choices
# we recognised while doing simple rendering for all others.
# 2. or, could define the type:choice and provide it as an
# extra field, but this means that the choice questions are
# slightly different objs than the others
default_questions = [
    {
        'question_text' : 'What is your business\'s name?',
        'key' : 'applicant_name',
        'type' : 'text',
        'required' : True
    },
    {
        'question_text' : 'What is your business\'s street address? (P.O. Box not accepted)',
        'key' : 'applicant_address',
        'type' : 'text',
        'required' : True
    },
    {
        'question_text' : 'What is the beneficiary (IE, the other party to this transaction)\'s name?',
        'key' : 'beneficiary_name',
        'type' : 'text',
        'required' : True
    },
    {
        'question_text' : 'What is the beneficiary\'s street address? (P.O. Box not accepted)',
        'key' : 'beneficiary_address',
        'type' : 'text',
        'required' : True
    },
    {
        'question_text' : 'Through what means will you forward the credit for this transaction, to either the beneficiary, SVB, or a bank selected by SVB? Standard options include S.W.I.F.T or Courier, but feel free to specify your own below.',
        'key' : 'credit_delivery_means',
        'type' : 'text',
        'required' : True
    },
    {
        'question_text' : 'What is the total size of this purchase, or the amount of credit you\'re seeking, in words?',
        'key' : 'credit_amt_verbal',
        'type' : 'text',
        'required' : True
    },
    {
        'question_text' : 'What is the total size of this purchase, or the amount of credit you\'re seeking, in figures?',
        'key' : 'credit_amt',
        'type' : 'decimal',
        'required' : True
    },
    {
        'question_text' : 'What currency is this purchase or credit denominated in?',
        'key' : 'currency_denomination',
        'type' : 'text',
        'required' : True
    },
    {
        'question_text' : 'Are you, the Applicant, requesting this Credit for account of an Account Party?',
        'key' : 'account_party',
        'type' : 'boolean',
        'required' : True
    },
    {
        'question_text' : 'Are you and any Account Party jointly and severally obligated?',
        'key' : 'applicant_and_ap_j_and_s_obligated',
        'type' : 'boolean',
        'required' : True
    },
    {
        'question_text' : 'If you, the Applicant, are not the Account Party, what is the Account Party\'s name?',
        'key' : 'account_party_name',
        'type' : 'text',
        'required' : False
    },
    {
        'question_text' : 'If you, the Applicant, are not the Account Party, what is the Account Party\'s address?',
        'key' : 'account_party_address',
        'type' : 'text',
        'required' : False
    },
    {
        'question_text' : 'If the beneficiary specified an Advising Bank, who is the Advising Bank? If not, the bank issuing this LC will serve as one or select one. You may also specify None to indicate a specific desire against having one.',
        'key' : 'advising_bank',
        'type' : 'text',
        'required' : False
    },
    {
        'question_text' : 'If you and your beneficiary established a Foreign Exchange Contract, what is the Foreign Exchange Contract Number?',
        'key' : 'forex_contract_num',
        'type' : 'text',
        'required' : False
    },
    {
        'question_text' : 'What percentage of currency exchange rate change will you tolerate? If you have secured a Foreign Exchange Contract, put 0%',
        'key' : 'exchange_rate_tolerance',
        'type' : 'decimal',
        'required' : True
    },
    {
        'question_text' : 'What good or service are you purchasing?',
        'key' : 'purchased_item',
        'type' : 'text',
        'required' : True
    },
    {
        'question_text' : 'What is the unit of measure of your purchase? IE - barrels, pounds, logs, or service contract',
        'key' : 'unit_of_measure',
        'type' : 'text',
        'required' : True
    },
    {
        'question_text' : 'How many units are you purchasing?',
        'key' : 'units_purchased',
        'type' : 'decimal',
        'required' : True
    },
    {
        'question_text' : 'What percentage of error in the received units will you tolerate?',
        'key' : 'unit_error_tolerance',
        'type' : 'decimal',
        'required' : True
    },
    {
        'question_text' : 'How would you like the payout of this transaction to be confirmed? Submit \'No Confirmation\' to indicate no need to confirm, or name the bank your beneficiary selected to confirm if they provided one. Alternatively, you can submit \'Confirmation by a bank of your choice\', and the bank issuing this LC will select a bank in the beneficiary\'s home country to confirm.',
        'key' : 'confirmation_means',
        'type' : 'text',
        'required' : True
    },
    {
        'question_text' : 'All of the issuing bank\'s charges will be paid by you, the Applicant. Who should pay charges from other banks party to this transaction? Choose either yourself, or the beneficiary.',
        'key' : 'paying_other_banks_fees',
        'type' : 'text',
        'required' : True
    },
    {
        'question_text' : 'Where should the Credit expire - or in other words, where must the documentary requirements be presented prior to the credit\'s expiration date? Choose either the confirming bank\'s office, or your issuing bank\'s office',
        'key' : 'credit_expiry_location',
        'type' : 'text',
        'required' : True
    },
    {
        'question_text' : 'What is the Expiration Date?',
        'key' : 'expiration_date',
        'type' : 'date',
        'required' : True
    },
    {
        'question_text' : 'When should drafts be presented? If not specified, we will default to 21 days after the date of shipment. This date must be prior to expiration of the LC.',
        'key' : 'draft_presentation_date',
        'type' : 'date',
        'required' : False
    },
    {
        'question_text' : 'What percentage of invoice value should Drafts include? We will use 100% if not otherwise specified',
        'key' : 'drafts_invoice_value',
        'type' : 'decimal',
        'required' : False
    },
    {
        'question_text' : 'How would you like to make Credit available? Standard options include payment at sight, acceptance some number of days after sight, acceptance some number of days after the agreed shipment date, acceptance some number of days after the agreed invoice date, and acceptance some number of days after the agreed draft date. Feel free to specify some other alternative.',
        'key' : 'credit_availability',
        'type' : 'text',
        'required' : True
    },
    {
        'question_text' : 'Who are acceptance and discount charges for the account of - you, the Applicant, or the Beneficiary?',
        'key' : 'paying_acceptance_and_discount_charges',
        'type' : 'text',
        'required' : True
    },
    {
        'question_text' : 'When may Deferred payment take place (the maturity date of the deferred payment obligation)?',
        'key' : 'deferred_payment_date',
        'type' : 'date',
        'required' : True
    },
    {
        'question_text' : 'What bank(s) do you authorise to negotiate deferred payment?',
        'key' : 'delegated_negotiating_banks',
        'type' : 'text',
        'required' : True
    },
    {
        'question_text' : 'Would you permit partial shipment?',
        'key' : 'partial_shipment_allowed',
        'type' : 'boolean',
        'required' : True
    },
    {
        'question_text' : 'Would you permit partial transshipment?',
        'key' : 'transshipment_allowed',
        'type' : 'boolean',
        'required' : True
    },
    {
        'question_text' : 'Where should merchandise be shipped or dispatched from/taken in charge at?',
        'key' : 'merch_charge_location',
        'type' : 'text',
        'required' : True
    },
    {
        'question_text' : 'If applicable, what is the latest date merchandise should be taken charge of?',
        'key' : 'late_charge_date',
        'type' : 'date',
        'required' : False
    },
    {
        'question_text' : 'Where will merchandise be transported to, once taken charge of?',
        'key' : 'charge_transportation_location',
        'type' : 'text',
        'required' : True
    },
    {
        'question_text' : 'For terms of shipment, what mode of transport, if any, should be shown on the Commercial Invoice? Options for general modes include EXW, FCA, CPT, CIP, DAT, DAP, and DDP. Options for sea and inland waterway transport include FAS, FOB, CFR, and CIF.',
        'key' : 'incoterms_to_show',
        'type' : 'text',
        'required' : True
    },
    {
        'question_text' : 'What is the named place of destination?',
        'key' : 'named_place_of_destination',
        'type' : 'text',
        'required' : True
    },
    {
        'question_text' : 'Should Drafts be accompanied by the Original, and/or a copy, of the Signed Commercial Invoice?',
        # options : Yes, Original || Yes, Original and Copy || No
        'key' : 'draft_accompiant_invoice',
        'type' : 'text',
        'required' : True
    },
    {
        'question_text' : 'What, if any, Transport Documents should accompany the Drafts?',
        # options : Full set original clean on board Marine Bills of Lading or multimodal or combined transport Bill of Lading issued to order of shipper, endorsed in blank || Clean Air Waybill consigned to the “Applicant” || Clean Truck / Rail Bill of Lading consigned to the “Applicant"
        'key' : 'draft_accompiant_transport_docs',
        'type' : 'text',
        'required' : False
    },
    {
        'question_text' : 'Who should be notified when Drafts and accompanying documents are received? We will notify the Applicant unless otherwise specified.',
        'key' : 'doc_reception_notifees',
        'type' : 'text',
        'required' : False
    },
    {
        'question_text' : 'Should the transport document be marked by Freight Collect, or Freight Prepaid? Skip to specify neither as necessary.',
        'key' : 'transport_doc_marking',
        'type' : 'text',
        'required' : False
    },
    {
        'question_text' : 'How many copies of the Packing List should accompany the Drafts? Select 0 or skip for none',
        'key' : 'copies_of_packing_list',
        'type' : 'number',
        'required' : False
    },
    {
        'question_text' : 'How many copies of the Certificate of Origin should accompany the Drafts? Select 0 or skip for none',
        'key' : 'copies_of_certificate_of_origin',
        'type' : 'number',
        'required' : False
    },
    {
        'question_text' : 'How many copies of the Inspection Certificate should accompany the Drafts? Select 0 or skip for none',
        'key' : 'copies_of_inspection_certificate',
        'type' : 'number',
        'required' : False
    },
    {
        'question_text' : 'If you\'d like your beneficiary to arrange insurance on this purchase, what percentage of the invoice value would you like to have insured by a Negotiable Inusrance Policy or Certificate? Specify 0% or skip if this is unnecessary for this transaction. 110% is standard.',
        'key' : 'insurance_percentage',
        'type' : 'decimal',
        'required' : False
    },
    {
        'question_text' : 'If you\'d like your beneficiary to arrange insurance on this purchase, what risks should it cover? Options include Marine Risk, Air Risk, War Risk, Theft/Pilferage/Non-Delivery Risks, and All Risks. Add any other risks you\'d like covered, and we will discuss.',
        'key' : 'insurance_risks_covered',
        'type' : 'text',
        'required' : False
    },
    {
        'question_text' : 'Are there any other documents which you\'d like the Drafts to be accompanied with?',
        'key' : 'other_draft_accompiants',
        'type' : 'text',
        'required' : False
    },
    {
        'question_text' : 'Will you, the Applicant, arrange your own insurance? If not, you should request evidence of insurance from the Beneficiary as documents to accompany the Drafts.',
        'key' : 'arranging_own_insurance',
        'type' : 'boolean',
        'required' : True
    },
    {
        'question_text' : 'Are there any other instructions you\'d like to include?',
        'key' : 'other_instructions',
        'type' : 'text',
        'required' : False
    },
    {
        'question_text' : 'Please describe the merchandise',
        'key' : 'merch_description',
        'type' : 'text',
        'required' : True
    },
    {
        'question_text' : 'Should this Credit be transferable, and if so, should it be transferable to the Applicant or Beneficiary\'s account?',
        'key' : 'transferability',
        'type' : 'text',
        'required' : True
    }
]
