from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.http import HttpResponseBadRequest, Http404, HttpResponseForbidden
from django.core import serializers
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from .models import LC, PdfLC, DigitalLC, LCAppQuestionResponse, DocumentaryRequirement
import json, datetime

# TODO only handling DigitalLCs for now

# 1. GET all the lcs from this bank
# 2. POST
@csrf_exempt
def cr_lcs(request, bank_id):
    if request.method == "GET":
        this_banks_lcs = LC.objects.filter(issuer=bank_id)
        return JsonResponse(list(this_banks_lcs.values()), safe=False)
    elif request.method == "POST":
        try:
            bank = Bank.objects.get(id=bank_id)
        except Bank.DoesNotExist:
            return Http404("No bank with id " + bank_id + " found")
        if request.user.is_authenticated:
            json_data = json.loads(request.body)
            if bank.bankemployee_set.filter(email=request.user.username).exists():
                # 1. create the initial LC instance with parties, creating new
                #    accounts/inviting registrants where applicable
                lc = LC(issuer = bank)
                lc.tasked_issuer_employees.add(bank.bankemployee_set.get(email=request.user.username))
                email_msg = 'fill out your app '
                try:
                    lc.client = Business.objects.get(name=json_data['applicant'])
                    if lc.client.businessemployee_set.filter(email=json_data['applicant_employee_contact']).exists():
                        lc.tasked_client_employees.add(Business.businessemployee_set.get(email=json_data['applicant_employee_contact']))
                    else:
                        # TODO decide - either
                            # add to the email_msg 'set your employee account up at <insert employee registration link>'
                        # or return an error, since the business exists, so it
                        # was probably a mistyped email
                        pass
                except Business.DoesNotExist:
                    # TODO add to the email_msg 'set your business up at <insert business registration link>'
                    pass
                lc.save()
                email_msg += 'at https://bountium.org/lc/' + lc.id
                # 2. mail the applicant_employee_contact with a link to fill out
                #    the rest of the LC via:
                # TODO get this working
                # mail(to=json_data['applicant_employee_contact'], subject='Finish your LC on Bountium', body=email_msg)
                # 3. return... TODO something
                return HttpResponse("nice")
            elif BusinessEmployee.objects.filter(email=request.user.username).exists():
                employee_applying = BusinessEmployee.objects.get(email=request.user.username)
                # 1. for each of the default questions,
                #   a. get the value and
                #   b. do something with it
                #   c. remove it from the list

                # Questions 1 and 2
                applicant_name = json_data['applicant_name']
                applicant_address = json_data['applicant_address']
                # TODO check if applicant_name == employee_applying.employer.name &&
                #               applicant_address == employee_applying.employer
                #               create the lc and proceed
                #            else
                #               return forbidden
                lc = LC(issuer = bank)
                lc.client = employee_applying.employer
                del json_data['applicant_name']
                del json_data['applicant_address']

                # Questions 3 and 4
                beneficiary_name = json_data['beneficiary_name']
                beneficiary_address = json_data['beneficiary_address']
                # TODO if beneficiary.found, add them as lc.beneficiary
                #      else, create the Business and send invite

                # Question 5-8
                lc.credit_delivery_means = json_data['credit_delivery_means']
                lc.credit_amt_verbal = json_data['credit_amt_verbal']
                lc.credit_amt = json_data['credit_amt']
                lc.currency_denomination = json_data['currency_denomination']

                # Question 9
                if json_data['account_party']:
                    # Question 10-12
                    lc.applicant_and_ap_j_and_s_obligated = json_data['applicant_and_ap_j_and_s_obligated']
                    account_party_name = json_data['account_party_name']
                    account_party_address = json_data['account_party_address']
                    # TODO if account_party.found, add them as lc.account_party
                    #      else, create the Business and send invite

                # Question 13
                if 'advising_bank' in json_data:
                    bank_name = json_data['advising_bank']
                    # TODO if Bank.get(name=bank_name).found, add them as lc.advising_bank
                    #      else, create the Bank and send invite

                # Question 14
                if 'forex_contract_num' in json_data:
                    lc.forex_contract_num = json_data['forex_contract_num']

                # Question 15-20
                lc.exchange_rate_tolerance = json_data['exchange_rate_tolerance']
                lc.purchased_item = json_data['purchased_item']
                lc.unit_of_measure = json_data['unit_of_measure']
                lc.units_purchased = json_data['units_purchased']
                lc.unit_error_tolerance = json_data['unit_error_tolerance']
                lc.confirmation_means = json_data['confirmation_means']

                # TODO all the other questions

                # 2. for any other fields left in json_data, save them as a tuple
                #    in other_data

            else:
                # TODO minor, but, technically you can get to this branch by being
                # a BankEmployee of a bank other than bank_id.
                return HttpResponseForbidden("Only employees of businesses or banks on Bountium can create LCs")
        else:
            return HttpResponseForbidden("Must be logged in to create an LC")
    else:
        return HttpResponseBadRequest("This endpoint only supports GET, POST")
