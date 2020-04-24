from django.db import models
from bank.models import Bank, BankEmployee, LCAppQuestion
from business.models import Business, BusinessEmployee
from django.forms.models import model_to_dict
from fpdf import FPDF
import os, boto3, datetime

def writeln(pdf, str):
    pdf.cell(200, 10, txt=str, ln=1, align="L")

# TODO lc.client_approved might be redundant and in fact inconvenient if the client expects the issuer to handle negotiations

# Abstract LC from which Pdf and Digital inherit
class LC(models.Model):
    # -- the parties to an LC -- #
    client = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='%(app_label)s_%(class)s_client', null=True, blank=True)
    beneficiary = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='%(app_label)s_%(class)s_beneficiary', null=True, blank=True)
    issuer = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='%(app_label)s_%(class)s_issuer')
    account_party = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='%(app_label)s_%(class)s_account_party', null=True, blank=True)
    advising_bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='%(app_label)s_%(class)s_advising_bank', null=True, blank=True)

    # -- employees of the parties assigned -- #
    tasked_client_employees = models.ManyToManyField(BusinessEmployee, related_name='%(app_label)s_%(class)s_tasked_client_employees')
    tasked_beneficiary_employees = models.ManyToManyField(BusinessEmployee, related_name='%(app_label)s_%(class)s_tasked_beneficiary_employees')
    tasked_issuer_employees = models.ManyToManyField(BankEmployee, related_name='%(app_label)s_%(class)s_tasked_issuer_employees')
    tasked_account_party_employees = models.ManyToManyField(BusinessEmployee, related_name='%(app_label)s_%(class)s_tasked_account_party_employees')
    tasked_advising_bank_employees = models.ManyToManyField(BankEmployee, related_name='%(app_label)s_%(class)s_tasked_advising_bank_employees')

    # -- the status of an LC -- #
    client_approved = models.BooleanField(default=True)
    issuer_approved = models.BooleanField(default=False)
    beneficiary_approved = models.BooleanField(default=False)
    # of the form 'On XXX date, [beneficiary or issuer] disapproved, saying:'
    latest_version_notes = models.CharField(max_length=1000, null=True, blank=True)
    #TODO: previous_version = models.ForeignKey(LC, )

    # TODO do terms_satisfied & paid_out fields make sense for a Standby LC?
    # theoretically it could be 'satisfied' and 'pay out more than once' -
    # the difference is, of course, that satisfaction is a bad thing
    # and not expected.
    application_date = models.DateField(blank=True, null=True)
    terms_satisfied = models.BooleanField(default=False)
    requested = models.BooleanField(default=False)
    drawn = models.BooleanField(default=False)
    paid_out = models.BooleanField(default=False)

    # Using because django's JSON serialiser doesnt like nested
    # serialising into LCAppQuestion
    def to_dict(self):
        return self.get_base_fields()

    def get_base_fields(self):
        to_return = {
            'id' : self.id,
            'issuer' : self.issuer.to_dict(),
            'tasked_client_employees' : self.get_tasked_client_employees(),
            'tasked_beneficiary_employees' : self.get_tasked_beneficiary_employees(),
            'tasked_issuer_employees' : self.get_tasked_issuer_employees(),
            'tasked_account_party_employees' : self.get_tasked_account_party_employees(),
            'tasked_advising_bank_employees' : self.get_tasked_advising_bank_employees(),
            'client_approved' : self.client_approved,
            'beneficiary_approved' : self.beneficiary_approved,
            'issuer_approved' : self.issuer_approved,
            'latest_version_notes' : self.latest_version_notes,
            'application_date' : self.application_date,
            'terms_satisfied' : self.terms_satisfied,
            'requested' : self.requested,
            'drawn' : self.drawn,
            'paid_out' : self.paid_out,
            'documentaryrequirement_set' : self.get_doc_reqs()
        }
        if self.client:
            to_return['client'] = model_to_dict(self.client)
        if self.beneficiary:
            to_return['beneficiary'] = model_to_dict(self.beneficiary)
        if self.account_party:
            to_return['account_party'] = model_to_dict(self.account_party)
        if self.advising_bank:
            to_return['advising_bank'] = self.advising_bank.to_dict()
        return to_return

    # TODO TODO TODO
    # the following 5 methods can almost certainly be consolidated into 1
    # which received tasked_X_employees as a parameter, but im speed-running rn
    def get_tasked_client_employees(self):
        to_return = []
        for employee in self.tasked_client_employees.all():
            to_return.append(model_to_dict(employee))
        return to_return

    def get_tasked_beneficiary_employees(self):
        to_return = []
        for employee in self.tasked_beneficiary_employees.all():
            to_return.append(model_to_dict(employee))
        return to_return

    def get_tasked_issuer_employees(self):
        to_return = []
        for employee in self.tasked_issuer_employees.all():
            to_return.append(model_to_dict(employee))
        return to_return

    def get_tasked_account_party_employees(self):
        to_return = []
        for employee in self.tasked_account_party_employees.all():
            to_return.append(model_to_dict(employee))
        return to_return

    def get_tasked_advising_bank_employees(self):
        to_return = []
        for employee in self.tasked_advising_bank_employees.all():
            to_return.append(model_to_dict(employee))
        return to_return

    def get_doc_reqs(self):
        to_return = []
        for doc_req in self.documentaryrequirement_set.all():
            to_return.append(doc_req.to_dict())
        return to_return

def pdf_app_response_path(lc, filename):
    # file will be uploaded to MEDIA_ROOT/bank_<id>/client_<id>/applications/%Y/%m/%d/filename
    return 'bank_{0}/client_{1}/applications/%Y/%m/%d/{2}'.format(instance.lc.issuer.id, instance.lc.client.id, filename)

def pdf_lc_contract_path(lc, filename):
    # file will be uploaded to MEDIA_ROOT/bank_<id>/client_<id>/contracts/%Y/%m/%d/filename
    return 'bank_{0}/client_{1}/contracts/%Y/%m/%d/{2}'.format(instance.lc.issuer.id, instance.lc.client.id, filename)

class PdfLC(LC):
    app_response = models.FileField(upload_to=pdf_app_response_path)
    contract = models.FileField(upload_to=pdf_lc_contract_path)

# TODO not using all fields in doc reqs; not all of them used in UCP 600 even
# though they do all appear in SVBs app. Figure out why, and perhaps differentiate
# between is_ucp_valid and all_fields_valid
class DigitalLC(LC):
    # TODO this should technically be an enum, one of
    # ['Commercial', 'Standby', 'Import', 'Export']
    type = models.CharField(max_length=20, default='Commercial')

    # -- the user-provided data of this lc per our default questions -- #
    # CDM can be ('Courier', 'SWIFT') or other
    credit_delivery_means = models.CharField(max_length=250, null=True, blank=True)
    credit_amt_verbal = models.CharField(max_length=250, null=True, blank=True)
    # Goes up to 999B,999M,999K,999.99
    credit_amt = models.DecimalField(max_digits=17, decimal_places=2, null=True, blank=True)
    # TODO this should technically be an enum
    currency_denomination = models.CharField(max_length=5, default='USD')
    applicant_and_ap_j_and_s_obligated = models.BooleanField(null=True, blank=True)
    forex_contract_num = models.CharField(max_length=250, null=True, blank=True)
    # 100.00000 -> 0.00000, where 100.00000 == 100% on user input
    exchange_rate_tolerance = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)
    purchased_item = models.CharField(max_length=1000, null=True, blank=True)
    unit_of_measure = models.CharField(max_length=1000, null=True, blank=True)
    # Goes up to 999T,999B,999M,999K,999.99
    units_purchased = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    # 100.00000 -> 0.00000, where 100.00000 == 100% on user input
    unit_error_tolerance = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)
    # NOTE this might be converted to an enum
    # One of:
    # ["No Confirmation",
    # "Confirmation by a bank selected by the beneficiary",
    # "Confirmation by a bank selected by SVB in the beneficiary\'s country"]
    confirmation_means = models.CharField(max_length=1000, default='No Confirmation')
    # almost always either the applicant or the beneficiary
    paying_other_banks_fees = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='%(app_label)s_%(class)s_paying_other_banks_fees', null=True, blank=True)
    # almost always the issuer or the confirming bank
    credit_expiry_location = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='%(app_label)s_%(class)s_credit_expiry_location', null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    draft_presentation_date = models.DateField(null=True, blank=True)
    # 100.00000 -> 0.00000, where 100.00000 == 100% on user input
    drafts_invoice_value = models.DecimalField(max_digits=8, decimal_places=5, default=1.00000)
    credit_availability = models.CharField(max_length=250, null=True, blank=True)
    paying_acceptance_and_discount_charges = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='%(app_label)s_%(class)s_paying_acceptance_and_discount_charges', null=True, blank=True)
    deferred_payment_date = models.DateField(null=True, blank=True)
    delegated_negotiating_banks = models.ManyToManyField(Bank)
    # TODO if partial_shipment_allowed, then we should accept MULTIPLE of each
    # documentary requirement, especially the transport ones, and not be
    # satisfied until their stated units / credit add up to the one asked for
    # in this LC, tolerance % permitting
    partial_shipment_allowed = models.BooleanField(default=False)
    transshipment_allowed = models.BooleanField(default=False)
    merch_charge_location = models.CharField(max_length=250, null=True, blank=True)
    late_charge_date = models.DateField(null=True, blank=True)
    charge_transportation_location = models.CharField(max_length=250, null=True, blank=True)
    # NOTE list, stored as string of JSON array of strings
    incoterms_to_show = models.CharField(max_length=250, null=True, blank=True)
    named_place_of_destination = models.CharField(max_length=250, null=True, blank=True)
    # TODO should this be a ManyToManyField on Business????
    doc_reception_notifees = models.CharField(max_length=250, null=True, blank=True)
    arranging_own_insurance = models.BooleanField(default=False)
    other_instructions = models.CharField(max_length=2000, null=True, blank=True)
    merch_description = models.CharField(max_length=2000, null=True, blank=True)
    # 0-1 of the following two fields can be true - not both
        # TODO is that constraint worth enforcing?
    transferable_to_applicant = models.BooleanField(default=False)
    transferable_to_beneficiary = models.BooleanField(default=False)

    # -- any other data this bank set up to ask for -- $
    # TODO saving as json obj string for now
    other_data = models.CharField(max_length=1000)

    # TODO someday: def to_pdf()

    # Overriding the above to add more fields
    def to_dict(self):
        to_return = self.get_base_fields()
        to_return.update({
            'type' : self.type,
            'credit_delivery_means' : self.credit_delivery_means,
            'credit_amt_verbal' : self.credit_amt_verbal,
            'credit_amt' : self.credit_amt,
            'currency_denomination' : self.currency_denomination,
            'applicant_and_ap_j_and_s_obligated' : self.applicant_and_ap_j_and_s_obligated,
            'forex_contract_num' : self.forex_contract_num,
            'exchange_rate_tolerance' : self.exchange_rate_tolerance,
            'purchased_item' : self.purchased_item,
            'unit_of_measure' : self.unit_of_measure,
            'units_purchased' : self.units_purchased,
            'unit_error_tolerance' : self.unit_error_tolerance,
            'confirmation_means' : self.confirmation_means,
            'expiration_date' : self.expiration_date,
            'draft_presentation_date' : self.draft_presentation_date,
            'drafts_invoice_value' : self.drafts_invoice_value,
            'credit_availability' : self.credit_availability,
            'deferred_payment_date' : self.deferred_payment_date,
            'delegated_negotiating_banks' : self.get_delegated_negotiating_banks(),
            'partial_shipment_allowed' : self.partial_shipment_allowed,
            'transshipment_allowed' : self.transshipment_allowed,
            'merch_charge_location' : self.merch_charge_location,
            'late_charge_date' : self.late_charge_date,
            'charge_transportation_location' : self.charge_transportation_location,
            'incoterms_to_show' : self.incoterms_to_show,
            'named_place_of_destination' : self.named_place_of_destination,
            'doc_reception_notifees' : self.doc_reception_notifees,
            'arranging_own_insurance' : self.arranging_own_insurance,
            'other_instructions' : self.other_instructions,
            'merch_description' : self.merch_description,
            'transferable_to_applicant' : self.transferable_to_applicant,
            'transferable_to_beneficiary' : self.transferable_to_beneficiary,
            'other_data' : self.other_data
        })
        if self.paying_other_banks_fees:
            to_return['paying_other_banks_fees'] = model_to_dict(self.paying_other_banks_fees)
        if self.credit_expiry_location:
            to_return['credit_expiry_location'] = self.credit_expiry_location.to_dict()
        if self.paying_acceptance_and_discount_charges:
            to_return['paying_acceptance_and_discount_charges'] = model_to_dict(self.paying_acceptance_and_discount_charges)
        return to_return

    def get_delegated_negotiating_banks(self):
        to_return = []
        for bank in self.delegated_negotiating_banks.all():
            to_return.append(bank.to_dict())
        return to_return

class LCAppQuestionResponse(models.Model):
    for_question = models.ForeignKey(LCAppQuestion, on_delete=models.CASCADE)
    for_lc = models.ForeignKey(DigitalLC, on_delete=models.CASCADE)
    raw_json_value = models.CharField(max_length = 5000)

class DocumentaryRequirement(models.Model):
    for_lc = models.ForeignKey(LC, on_delete=models.CASCADE)
    doc_name = models.CharField(max_length=250)
    # NOTE for now just letting users define the required values
    # as a string, ie:
        # "The inspection grade must be a B+ or higher"
    # enabling manual evaluation. down the line,
    # we should store a mapping of
        # "required_value_name : required_value_value"
    # so that we could intelligently scan a submitted doc req
    # for this value
    required_values = models.CharField(max_length=500, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    link_to_submitted_doc = models.CharField(max_length=250, null=True, blank=True)
    satisfied = models.BooleanField(default=False)
    submitted_doc_complaints = models.CharField(max_length=1000, null=True, blank=True)
    modified_and_awaiting_beneficiary_approval = models.BooleanField(default=False)
    modification_complaints = models.CharField(max_length=1000, null=True, blank=True)
    rejected = models.BooleanField(default=False)
    type = models.CharField(max_length=50, default='generic')

    def to_dict(self):
        return {
            'id' : self.id,
            'doc_name' : self.doc_name,
            'required_values' : self.required_values,
            'due_date' : self.due_date,
            'link_to_submitted_doc' : self.link_to_submitted_doc,
            'satisfied' : self.satisfied,
            'rejected' : self.rejected,
            'submitted_doc_complaints' : self.submitted_doc_complaints,
            'modified_and_awaiting_beneficiary_approval' : self.modified_and_awaiting_beneficiary_approval,
            'modification_complaints' : self.modification_complaints,
            'type' : self.type
        }

    def is_satisfied(self):
        return self.satisfied

# The following are specific standard documentary requirements which Bountium
# is prepared to more specifically analyse for compliance with the LCs terms.

# TODO most of these have the requirement that the bank must have all originals.
# How do we allow a user to indiciate this (perhaps just trust them to input it honestly)?
# And how does it apply to electronic documents?

# A beneficiary on Bountium can ensure their document's compliance by creating
# the doc in Bountium itself; in this case, the creation of each instance goes
# 1. populate the fields of the model,
# 2. run to_pdf to create the submitted_doc,
# 3. notify the issuer that they may examine for correctness but that it
# should be correct.

# If a beneficiary is submitting scanned / manually created documents, or the
# issuer is submitting on a snail-mailing beneficiary's behalf, then it goes
# 1. create the submitted_doc
# 2. allow the issuer to look at the doc in-app and set each field of the model
# based on their human analysis. over time we will upgrade this to
# software-aided, or better yet software-automated extraction of these values
# 3. notify everyone once the issuer makes an assessment, and that they should
# double check

# UCP 600, Article 18
# TODO need to cover part b somehow, integrating every bank's input
# TODO article 18 says nothing about unit amounts, tx size, etc (except somewhat in part b).
#      Should it? Does de facto interpretation?
#      i believe views.py is setting more required values than is captured by this/ucp600;
#      debate whether to go with the UCP 600 or logic, ask justin
class CommercialInvoiceRequirement(DocumentaryRequirement):
    seller_name = models.CharField(max_length=500, null=True, blank=True)
    seller_address = models.CharField(max_length=500, null=True, blank=True)
    indicated_date_of_shipment = models.DateField(blank=True, null=True)
    country_of_export = models.CharField(max_length=50, null=True, blank=True)
    incoterms_of_sale = models.CharField(max_length=50, null=True, blank=True)
    reason_for_export = models.CharField(max_length=50, default="Sale")

    consignee_name = models.CharField(max_length=500, null=True, blank=True)
    consignee_address = models.CharField(max_length=500, null=True, blank=True)
    buyer_name = models.CharField(max_length=500, null=True, blank=True)
    buyer_address = models.CharField(max_length=500, null=True, blank=True)

    # These are product params - some purchases some day will have more than 1 product per CI, but for now we assume theres 1 per
    units_purchased = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    unit_of_measure = models.CharField(max_length=1000, null=True, blank=True)
    goods_description = models.CharField(max_length=500, null=True, blank=True)
    # 5 char heading 4 digits then a period, ie 0302. Fish, fresh or chilled, excluding fish fillets and other fish meat
    # 5 char heading - 2x2 digits separated by a period then a period, ie 11.00. Trout (Salmo trutta)
    # 2 digit stat suffix ie 10 for Rainbow trout (salmo gairdneri), farmed
    hs_code = models.CharField(max_length=12, null=True, blank=True)
    country_of_origin = models.CharField(max_length=50, null=True, blank=True)
    unit_price = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    additional_comments = models.CharField(max_length=1000, null=True, blank=True)
    declaration_statement = models.CharField(max_length=1000, null=True, blank=True)
    currency = models.CharField(max_length=10, null=True, blank=True)

    signature = models.CharField(max_length=50, null=True, blank=True)
    signatory_title = models.CharField(max_length=50, null=True, blank=True)
    date_of_issuance = models.DateField(blank=True, null=True)

    def is_satisfied(self):
        return super().is_satisfied() or self.is_ucp_satisfied()

    def avoids_conflict_of_non_ucp_terms(self):
        # TODO
        return (

        )

    def is_ucp_satisfied(self):
        return (
            # TODO exact matches of the following 2 i unlikely -
            # ask justin how they enforce this
            self.seller_name == self.for_lc.beneficiary.name and
            self.buyer_name == self.for_lc.client.name and
            self.currency == self.for_lc.currency_denomination and
            # TODO this demands an exact match, which is unlikely for prose! ask justin
            self.goods_description == self.for_lc.goods_description and
            self.signature
        )

    def generate_pdf(self):
        self.date_of_issuance = datetime.datetime.now()
        created_doc_name = "commercial-invoice-from " + self.seller_name + "-on-" + str(self.date_of_issuance) + ".pdf"
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Times", size=24)
        pdf.cell(200, 20, txt="Commercial Invoice", ln=1, align="C")
        pdf.set_font("Times", size=12)
        # TODO how to make multi cells line up horizontally
        pdf.multi_cell(border=1, w=90, h=6, txt=(
            "Seller name: " + self.seller_name +
            "\nSeller address: " + self.seller_address +
            "\nShipped on: " + self.indicated_date_of_shipment +
            "\nCountry of Export: " + self.country_of_export +
            "\nIncoterms of sale: " + str(self.incoterms_of_sale) +
            "\nReason for export: " + self.reason_for_export
        ))
        """pdf.multi_cell(border=1, w=90, h=6, txt=(

        ))"""
        if self.consignee_name and self.consignee_address:
            pdf.multi_cell(border=1, w=90, h=6, txt=(
                "Consignee name: " + self.consignee_name +
                "\nConsignee address: " + self.consignee_address
            ))
        else:
            pdf.multi_cell(border=1, w=90, h=6, txt=(
                "Consignee name: " + self.buyer_name +
                "\nConsignee address: " + self.buyer_address
            ))
        pdf.multi_cell(border=1, w=90, h=6, txt=(
            "Buyer name: " + self.buyer_name +
            "\nBuyer address: " + self.buyer_address
        ))
        writeln(pdf, "Goods Description:")
        # TODO need to somehow make this a paragraph instead of a line
        writeln(pdf, self.goods_description)
        writeln(pdf, "Units of measure: " + self.unit_of_measure)
        writeln(pdf, "Units purchased: " + str(self.units_purchased))
        writeln(pdf, "Price per unit: " + str(self.unit_price))
        writeln(pdf, "Currency of settlement: " + self.currency)
        writeln(pdf, "Harmonized Schedule Code: " + self.hs_code)
        writeln(pdf, "Country of Origin: " + self.country_of_origin)
        writeln(pdf, "Total purchase value: " + str(self.unit_price * self.units_purchased))
        writeln(pdf, "Payment method: L/C")
        # TODO need to somehow make this a paragraph instead of a line
        writeln(pdf, "Additional comments: " + self.additional_comments)
        # TODO need to somehow make this a paragraph instead of a line
        writeln(pdf, "Declaration statements: " + self.declaration_statement)
        writeln(pdf, "The undersigned declares all the information contained in this invoice to be true and correct:")
        writeln(pdf, self.signature)
        writeln(pdf, self.signatory_title)
        writeln(pdf, "Date: " + str(self.date_of_issuance))
        pdf.output(created_doc_name)
        s3 = boto3.resource('s3')
        s3.Bucket('docreqs').put_object(Key=created_doc_name, Body=open(created_doc_name, 'rb'))
        self.link_to_submitted_doc = "https://docreqs.s3.us-east-2.amazonaws.com/" + created_doc_name
        os.remove(created_doc_name)

def create_test_ci():
    test_ci = CommercialInvoiceRequirement(
        for_lc=LC.objects.get(id=1),
        seller_name="bean corp",
        seller_address="123 bean st",
        indicated_date_of_shipment="04-23-2020",
        country_of_export="USA",
        incoterms_of_sale="FAX",
        currency="USD",
        consignee_name="bean consignee",
        consignee_address="234 bean ave",
        buyer_name="bean purchaser",
        buyer_address="345 bean boulevard",
        goods_description="_hella_ good beans",
        reason_for_export="Sale",
        unit_of_measure="Barrels",
        units_purchased=400,
        unit_price=0.1,
        hs_code="0713330000",
        country_of_origin="USA",
        additional_comments="make them... beansy",
        declaration_statement="I. Declare. Beans",
        signature="Steve Flanagan",
        signatory_title="Beansman"
    )
    test_ci.generate_pdf()

# For the following transport docs 19-25, articles 26 and 27 apply -
# 26: a) must not be loaded on deck, b) bear a clause such as "shipper's load and count"
# and "said by shipper to contain", c) something about charges?
# 27: must be clean
# TODO many fields of children are ~analogous~ but not exactly the same;
# charge_location is the same as a port_of_loading, for example. What are the
# pros and cons of abstracting these?
class TransportDocumentRequirement(DocumentaryRequirement):
    # seemingly can be anything except blank
    carrier_name = models.CharField(max_length=500, null=True, blank=True)
    # should be true, seemingly must be done by human inspection, agent is
    # permitted to sign if they indicate for whom they sign. signatory must
    # indicate if they're the carrier or master.
    signed_by_carrier_or_master = models.BooleanField(default=False)
    # should be True
    references_tandc_of_carriage = models.BooleanField(default=False)
    # one of these should be <= late_charge_date. if both non-null use the
    # indicated_date_of_shipment - the latter might not be present
    # transport by courier or multimodal will use stamps for this
    date_of_issuance = models.DateField(blank=True, null=True)
    indicated_date_of_shipment = models.DateField(blank=True, null=True)

    def basics_satisfied(self):
        return (
            self.carrier_name and
            self.signed_by_carrier_or_master and
            self.references_tandc_of_carriage and
            ((self.indicated_date_of_shipment and (self.indicated_date_of_shipment <= self.for_lc.late_charge_date))
            or (self.date_of_issuance <= self.for_lc.late_charge_date))
        )

# UCP 600, Article 19
# TODO the last part - cii - seems to say that a transport doc which allows
#      transshipment, even if !transshipment_allowed on the lc's terms,
#      should be accepted. ask justin if thats accurate, and if so, why SVB
#      bothers asking clients the question
class MultimodalTransportDocumentRequirement(TransportDocumentRequirement):
    carrier_address = models.CharField(max_length=500, null=True, blank=True)
    consignee_name = models.CharField(max_length=500, null=True, blank=True)
    consignee_address = models.CharField(max_length=500, null=True, blank=True)
    notifee_name = models.CharField(max_length=500, null=True, blank=True)
    notifee_address = models.CharField(max_length=500, null=True, blank=True)

    vessel_and_voyage = models.CharField(max_length=500, null=True, blank=True)
    place_of_dispatch = models.CharField(max_length=500, null=True, blank=True)
    port_of_loading = models.CharField(max_length=500, null=True, blank=True)
    port_of_discharge = models.CharField(max_length=500, null=True, blank=True)
    place_of_destination = models.CharField(max_length=500, null=True, blank=True)
    subject_to_charter_party = models.BooleanField(default=False)

    container_id = models.CharField(max_length=500, null=True, blank=True)
    goods_description = models.CharField(max_length=500, null=True, blank=True)
    # either "Prepaid" or "Collect"
    freight_payment = models.CharField(max_length=20, null=True, blank=True)
    gross_weight = models.CharField(max_length=30, null=True, blank=True)

    signature = models.CharField(max_length=50, null=True, blank=True)
    signatory_title = models.CharField(max_length=50, null=True, blank=True)

    def is_satisfied(self):
        return super().is_satisfied() or (
            self.basics_satisfied() and
            self.charge_location == self.for_lc.merch_charge_location and
            self.place_of_dispatch == self.for_lc.merch_charge_location and
            self.place_of_destination == self.for_lc.charge_transportation_location and
            not self.subject_to_charter_party
        )

    def generate_pdf(self):
        self.date_of_issuance = datetime.datetime.now()
        created_doc_name = "multimodal-bl-from " + self.carrier_name + "-on-" + str(self.date_of_issuance) + ".pdf"
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Times", size=24)
        pdf.cell(200, 20, txt="Multiomodal Bill of Lading", ln=1, align="C")
        pdf.set_font("Times", size=12)
        # TODO how to make multi cells line up horizontally
        pdf.multi_cell(border=1, w=90, h=6, txt=(
            "Shipper name: " + self.carrier_name +
            "\nShipper address: " + self.carrier_address +
            "\nShipped on: " + self.indicated_date_of_shipment
        ))
        pdf.multi_cell(border=1, w=90, h=6, txt=(
            "Consignee name: " + self.consignee_name +
            "\nConsignee address: " + self.consignee_address
        ))
        pdf.multi_cell(border=1, w=90, h=6, txt=(
            "Notifee name: " + self.notifee_name +
            "\nNotifee address: " + self.notifee_address
        ))
        if self.vessel_and_voyage:
            writeln(pdf, "Vessel and voyage: " + self.vessel_and_voyage)
        pdf.multi_cell(border=1, w=180, h=6, txt=(
            "Place of dispatch: " + self.place_of_dispatch +
            "\nPort of loading: " + str(self.port_of_loading) +
            "\nPort of discharge: " + str(self.port_of_discharge) +
            "\nPlace of receipt: " + self.place_of_destination
        ))
        if self.subject_to_charter_party:
            writeln(pdf, "Subject to charty party: Yes")
        else:
            writeln(pdf, "Subject to charty party: No")
        writeln(pdf, "Container id: " + self.container_id)
        writeln(pdf, "Goods Description:")
        # TODO need to somehow make this a paragraph instead of a line
        writeln(pdf, self.goods_description)
        writeln(pdf, "Freight payment: " + self.freight_payment)
        writeln(pdf, "Gross weight: " + self.gross_weight)
        writeln(pdf, "Payment method: L/C")
        writeln(pdf, "The undersigned declares all the information contained in this invoice to be true and correct:")
        writeln(pdf, self.signature)
        writeln(pdf, self.signatory_title)
        writeln(pdf, "Date: " + str(self.date_of_issuance))
        pdf.output(created_doc_name)
        s3 = boto3.resource('s3')
        s3.Bucket('docreqs').put_object(Key=created_doc_name, Body=open(created_doc_name, 'rb'))
        self.link_to_submitted_doc = "https://docreqs.s3.us-east-2.amazonaws.com/" + created_doc_name
        os.remove(created_doc_name)

def create_test_multimodal_bl():
    test_multiomodal_bl = MultimodalTransportDocumentRequirement(
        for_lc=LC.objects.get(id=1),
        carrier_name="bean corp",
        carrier_address="123 bean st",
        indicated_date_of_shipment="04-24-2020",
        consignee_name="bean consignee",
        consignee_address="234 bean ave",
        notifee_name="notify me about beans",
        notifee_address="345 bean boulevard",
        goods_description="_hella_ good beans",
        vessel_and_voyage = "SS bean dispatcher - NL739R",
        place_of_dispatch = "Needham",
        port_of_loading = "Boston",
        port_of_discharge = "Nice, France",
        place_of_destination = "Paris, France",
        subject_to_charter_party = False,
        container_id = "SSEGU5175079/40HC",
        freight_payment = "Collect",
        gross_weight = "21,000,000 KG",
        signature="Steve Flanagan",
        signatory_title="Beansman"
    )
    test_multiomodal_bl.generate_pdf()

# UCP 600, Article 20
class BillOfLadingRequirement(TransportDocumentRequirement):
    port_of_loading = models.CharField(max_length=500, null=True, blank=True)
    # this is part aii last paragraph - essentially, if the only provided bill
    # of lading says 'intended vessel' or something like that, the carrier
    # could switch the vessel and not provide any definitive answer as to what
    # vessel the goods got on when. This constraint ensures the bene cannot try
    # to keep things broad / nonspecific / noncommital, as a plan to retain deniability
    # in court.
    # This also applies to qualifiers put on the port of loading (part aiii)
    noncommital_shipment_indication_with_no_update = models.BooleanField(default=True)
    port_of_destination = models.CharField(max_length=500, null=True, blank=True)
    subject_to_charter_party = models.BooleanField(default=False)

    def is_satisfied(self):
        return super().is_satisfied() or (
            self.basics_satisfied() and
            self.port_of_loading == self.for_lc.merch_charge_location and
            not noncommital_shipment_indication_with_no_update and
            self.port_of_destination == self.for_lc.charge_transportation_location and
            not subject_to_charter_party
        )

# UCP 600, Article 21
# as far as i can tell, these have all the same fields, and the only difference
# is that the bill of lading is actually a deed to the goods. this difference
# will matter when we use blockchain BoL (ie, BoL will extend sea waybill and
# also have the token ID, indicating ownership, whereas the sea waybill will
# be purely for data)
class NonNegotiableSeaWaybillRequirement(BillOfLadingRequirement):
    pass

# UCP 600, Article 22
class CharterPartyBillOfLadingRequirement(DocumentaryRequirement):
    carrying_vessel = models.CharField(max_length=500, null=True, blank=True)
    signed_by_master_owner_charterer = models.BooleanField(default=False)
    port_of_loading = models.CharField(max_length=500, null=True, blank=True)
    # one of these should be <= late_charge_date. if both non-null use the
    # indicated_date_of_shipment - the latter might not be present
    date_of_issuance = models.DateField(blank=True, null=True)
    indicated_date_of_shipment = models.DateField(blank=True, null=True)
    # should be == charge_transportation_location
    # This can be a range of ports or a geographical area, unlike a regular BoL
    # - TODO how do we do that in code?
    port_of_destination = models.CharField(max_length=500, null=True, blank=True)

    def is_satisfied(self):
        return super().is_satisfied() or (
            self.carrying_vessel and
            self.signed_by_master_owner_charterer and
            self.port_of_loading == self.for_lc.merch_charge_location and
            ((self.indicated_date_of_shipment and (self.indicated_date_of_shipment <= self.for_lc.late_charge_date))
             or (self.date_of_issuance <= self.for_lc.late_charge_date)) and
            not noncommital_shipment_indication_with_no_update and
            self.port_of_destination == self.for_lc.charge_transportation_location
        )

# UCP 600, Article 23
class AirTransportDocument(TransportDocumentRequirement):
    accepted_for_carriage = models.BooleanField(default=False)
    airport_of_departure = models.CharField(max_length=500, null=True, blank=True)
    airport_of_destination = models.CharField(max_length=500, null=True, blank=True)

    def is_satisfied(self):
        return super().is_satisfied() or (
            self.basics_satisfied() and
            self.airport_of_departure == self.for_lc.merch_charge_location and
            self.airport_of_destination == self.for_lc.charge_transportation_location and
            not subject_to_charter_party
        )

# UCP 600, Article 24
class RoadRailInlandWaterwayTransportDocumentsRequirement(TransportDocumentRequirement):
    # rail transport documents specifically can substitute
    # signed_by_carrier_agent_or_master for stamped_by_rail_co
    stamped_by_rail_co = models.BooleanField(default=False)
    # should be = merch_charge_location and charge_transportation_location, respectively
    place_of_shipment = models.CharField(max_length=500, null=True, blank=True)
    place_of_destination = models.CharField(max_length=500, null=True, blank=True)

    def is_satisfied(self):
        return super().is_satisfied() or (
            ((self.carrier_name and self.signed_by_carrier_agent_or_master) or self.stamped_by_rail_co) and
            ((self.indicated_date_of_shipment and (self.indicated_date_of_shipment <= self.for_lc.late_charge_date))
            or (self.date_of_issuance <= self.for_lc.late_charge_date)) and
            self.place_of_shipment == self.for_lc.merch_charge_location and
            self.place_of_destination == self.for_lc.charge_transportation_location
        )

# UCP 600, Article 25 (for shipping via courier)
# TODO ask justin if this is for the courier carrying the credit or something else
class CourierReceiptRequirement(DocumentaryRequirement):
    courier_name = models.CharField(max_length=500, null=True, blank=True)
    stamped_or_signed_by_courier = models.BooleanField(default=False)
    stamping_or_signing_location = models.CharField(max_length=500, null=True, blank=True)
    date_of_pickup = models.DateField(blank=True, null=True)

    def is_satisfied(self):
        return super().is_satisfied() or (
            self.courier_name and
            self.stamped_or_signed_by_courier and
            stamping_or_signing_location == self.for_lc.merch_charge_location and
            self.date_of_pickup <= self.for_lc.late_charge_date
        )

# UCP 600, Article 25 (for confirming receipt via courier)
# TODO ask justin if this is for the courier carrying the credit or something else
class PostReceiptRequirement(DocumentaryRequirement):
    courier_name = models.CharField(max_length=500, null=True, blank=True)
    stamped_or_signed_by_courier = models.BooleanField(default=False)
    stamping_or_signing_location = models.CharField(max_length=500, null=True, blank=True)
    date_of_stamping = models.DateField(blank=True, null=True)

    def is_satisfied(self):
        return super().is_satisfied() or (
            self.courier_name and
            self.stamped_or_signed_by_courier and
            stamping_or_signing_location == self.for_lc.charge_transportation_location and
            self.date_of_stamping <= self.for_lc.late_charge_date
        )

# UCP 600, Article 28
class InsuranceDocumentRequirement(DocumentaryRequirement):
    # must be determined by a human analyst
    # TODO think through this better - part a)
    issued_by_insurer = models.BooleanField(default=False)
    # should be true, must be determined by human analyst
    # TODO wtf is a cover note lol
    is_not_cover_note = models.BooleanField(default=False)
    # either the document must be dated prior to shipment date, or
    # the policy's wording must indicate that the coverage was effective
    # prior to shipment
    covered_prior_to_shipment = models.BooleanField(default=False)
    # Goes up to 999T,999B,999M,999K,999.99
    # must be (requested_insurance_pct * credit_amt)
    coverage_amt = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    # TODO covered_locations, must be be between place of charge/shipment and
    # place of discharge / final destination
    # TODO covered_risks
    # TODO

# TODO packing list, certificate of origin
