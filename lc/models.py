from django.db import models
from bank.models import Bank, BankEmployee, LCAppQuestion
from business.models import Business, BusinessEmployee
from django.forms.models import model_to_dict

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
            to_return['advising_bank'] = model_to_dict(self.advising_bank)
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
    # 1.00000 -> 0.00000, where 1.00000 == 100% on user input
    exchange_rate_tolerance = models.DecimalField(max_digits=6, decimal_places=5, null=True, blank=True)
    purchased_item = models.CharField(max_length=1000, null=True, blank=True)
    units_of_measure = models.CharField(max_length=1000, null=True, blank=True)
    # Goes up to 999T,999B,999M,999K,999.99
    units_purchased = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    # 1.00000 -> 0.00000, where 1.00000 == 100% on user input
    unit_error_tolerance = models.DecimalField(max_digits=6, decimal_places=5, null=True, blank=True)
    # NOTE this might be converted to an enum
    # One of: ["No Confirmation", "Confirmation by a bank selected by the beneficiary", "Confirmation by a bank selected by SVB in the beneficiary\'s country"]
    confirmation_means = models.CharField(max_length=1000, default='No Confirmation')
    # almost always either the applicant or the beneficiary
    paying_other_banks_fees = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='%(app_label)s_%(class)s_paying_other_banks_fees', null=True, blank=True)
    # almost always the issuer or the confirming bank
    credit_expiry_location = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='%(app_label)s_%(class)s_credit_expiry_location', null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    draft_presentation_date = models.DateField(null=True, blank=True)
    # 1.00000 -> 0.00000, where 1.00000 == 100% on user input
    drafts_invoice_value = models.DecimalField(max_digits=6, decimal_places=5, default=1.00000)
    credit_availability = models.CharField(max_length=250, null=True, blank=True)
    paying_acceptance_and_discount_charges = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='%(app_label)s_%(class)s_paying_acceptance_and_discount_charges', null=True, blank=True)
    deferred_payment_date = models.DateField(null=True, blank=True)
    delegated_negotiating_banks = models.ManyToManyField(Bank)
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
            'units_of_measure' : self.units_of_measure,
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
            'modification_complaints' : self.modification_complaints
        }
