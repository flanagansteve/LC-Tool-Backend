from django.conf.urls import url

from . import views

""" Endpoints:
1. /lc/{lc_id}/ (a very busy endpoint lol)
# POST to respond to a created LC application
    # If
        !(<lc for which id == lc_id>.filledOut)
        && (<the employee POSTing>.employer == <lc for which id == lc_id>.applicant)
    we expect this to be the rest of the values required to create an LC - one of:
    <aFilledOutPDFApp.pdf>
    or, a JSON obj of the form
    {
        'string key of the application question' :
        <the user's response as a json string or int or whatever>
    }
    # receive back
    {
        'success' : true || false
    }
# PUT to update an LC
    # TODO update this ... now supports clients, now accepts update as
    {
        'lc' : {the new lc obj, possibly partial},
        'latest_version_notes' : 'latest version notes the user sbmitted with their update'
    }
    # If its a BusinessEmployee PUTing...
        # If
            !(<lc for which id == lc_id>.beneficiaryApproved)
            && (<the employee PUTing>.employer == <lc for which id == lc_id>.beneficiary)
        we expect this to be part of the redlining process, and thus, expect one of:
        [beneficiary_redlined_contract.pdf]
        or
        {
            [the updated fields of a digital LC model]
        }
        We will:
        1. update the LC to the version we just received
        2. mark it as beneficiary_approved = True
        3. notify the issuing bank and await their approval
    # If its a BankEmployee PUTing...
        # If
            (<lc for which id == lc_id>.approved)
            && (<the employee PUTing>.bank == <lc for which id == lc_id>.issuer)
        we expect this to be part of the redlining process, and thus, expect one of:
        [issuer_redlined_contract.pdf]
        or
        {
            [the updated fields of a digital LC model]
        }
        We will:
        1. update the LC to the version we just received
        2. mark it as issuer_approved = True
        3. notify the counterparty and await their approval
# GET, and receive back
{
    <the fields of a DigitalLC>,
    'other_data' : [
        {
            'one of the banks non-default questions ' :
            <the users raw json response>
        }
    ]
}
or
{
    <the fields of a PdfLC>
}

if you are an employee of the applicant, issuing bank, or beneficiary
# DeLETE, if
- you are the applicant or issuing bank, and
- the LC is not (beneficiary_approved && issuer_approved)
and receive back either
{
'success':true
} or
{
'success':false,
'reason':'This LC has been approved by both the issuer and beneficiary, and may not be revoked' ||
}
Note that an unsuccessful delete attempt is different from a bad request, forbidden, request, or 404. Its a *valid* 
request in the software, but a request we cannot honor in implementation.

2. /lc/by_bank/{bank_id}/
# GET all the lcs from this bank (TODO: thats probably just for testing)
# POST the following to create an LC at this bank
    # If its a BusinessEmployee POSTing, we expect one of
    <aFilledOutPDFApp.pdf>
    or, a JSON obj of the form
    {
        'string key of the application question' :
        <the user's response as a json string or int or whatever>
    }
    # and receive back
    {
        'success' : true || false,
        'created_lc' : {the lc obj you just made, with an id field}
    }
    # If its a BankEmployee POSTing, we expect
    [app_response_that_i_uploaded_on_behalf_of_a_client.pdf]
    or, for creating an LC app that your client will fill out later (which bountium will notify them about)
    {
        'applicant' : 'the applicants business name',
        'applicant_employee_contact' : 'someemployee@business.com'
        [we'll either create the Business in our database, or re-use if this is a repeat]
    }
    and receive back
    {
        'success' : true || false,
        'created_lc' : {the lc obj you just made, with an id field}
    }

3. /lc/by_bank/{bank_id}/{filter}/
# GET with a {filter}, and receive back a list of not-paid-out LCs issued by the specified bank
"live" : LCs that are approved by all parties

"awaiting_issuer_approval" : LCs that are issued (or requested to be issued via using their bountium-hosted application)

"awaiting_beneficiary_approval" : LCs that are not yet approved by the beneficiary

"awaiting_client_approval" : LCs that are not yet approved by the client

4. /lc/by_client/{business_id}/
# GET, and receive back a list of LCs that are
- credited from (or, if not yet approved, applied from) the business for which id=business_id

5. /lc/by_beneficiary/{business_id}/
# GET, and receive back a list of LCs that are
- credited to (or, if not yet approved, proposed-to-be-credited-to) the business for which id=business_id

6. /lc/{lc_id}/{state_to_mark}/
# POST as an employee of the beneficiary or issuer to update LC status:
"request" : request payment as beneficiary
"draw" : draw on the LC legally as beneficiary
"payout" : mark the Lc as paid out as issuer
"notify" : POST the following
{
    'to_notify' : 'email_of_teammate@issuingbank.com',
    'note' : 'optionally, send a note with the request'
}
# as an employee of the issuer, client, or beneficiary,
# to notify a teammate of some need on the LC.
# If the teammate is not yet assigned to this LC, this will assign them to it.
"evaluate" :  POST the following to approve of an LC, or disapprove with attached complaints during redlining, 
as either an employee of
    (<lc for which id == lc_id>.issuer)
or
    (<lc for which id == lc_id>.beneficiary)
{
    'approve': true || false,
    'complaints' : 'any complaints; blank if approve == true'
}

7. /lc/{lc_id}/claim/{relation}
# POST as a logged-in BusinessEmployee to claim one of the following relations to an LC:
- beneficiary
- account_party
- advising [as in, the advising bank]

8. /lc/{lc_id}/doc_req/
# POST the following
{
    'doc_name' : 'name_of_doc_req'
    'link_to_submitted_doc' : https://somecloudhost.com/link_to_the/file.pdf
}
as an employee of the beneficiary to create & submit a DocumentaryRequirement
    if its for a PdfLC we'll be creating the DocumentaryRequirement, and return a JSON response with its ID:
        {
            'doc_req_id' : int of the doc reqs id
        }
    if its for a DigitalLC we'll be adding this as an auxiliary DocumentaryRequirement, and return a JSON response 
    with its ID:
        {
            'doc_req_id' : int of the doc reqs id
        }
    NOTE: If you are submitting a doc req for an existing doc req you should PUT to /lc/{lc_id}/doc_req/{doc_req_id}
# GET the current doc reqs and statuses

9. /lc/{lc_id}/doc_req/{doc_req_id}/
# GET a doc req, whether or not a doc has been submitted yet

# PUT a submitted file to this as the beneficiary,
in the request body,
as content-type=application/pdf, and receive back
{
    'success':true || false,
    'modified_and_notified_on':str(datetime.datetime.now()),
    'doc_req':{the new doc_req's data and status}
}

# PUT {
    'due_date':int of the unix time of the new due date,
    'required_values':'a new required values str'
} as any party to the LC to update its terms, and receive back
{
    'success':true || false,
    'modified_and_notified_on':str(datetime.datetime.now()),
    'doc_req':{the new doc_req's data and status}
}

# DeLETE to delete a doc req as the issuer, and receive back
{
    'success': true || false,
    'doc_reqs':[{list of resultant doc reqs and their statuses}]
}

10. /lc/{lc_id}/doc_req/{doc_req_id}/evaluate/
# POST
- as an employee of the issuing bank to approve/dispute a DocumentaryRequirement's submitted_doc with
{
    'approve': true || false,
    'complaints' : 'any complaints; blank if approve == true'
}
and receive back
{
    'success': true || false,
    'doc_reqs':[{list of resultant doc reqs and their statuses}]
}
- as an employee of the beneficiary to approve/dispute any modifications made by the issuer to this doc req, 
if doc_req.modified_and_awaiting_beneficiary_approval, with
{
    'approve': true || false,
    'complaints' : 'any complaints; blank if approve == true'
}
and receive back
{
    'success': true || false,
    'doc_reqs':[{list of resultant doc reqs and their statuses}]
}

11. /lc/{lc_id}/doc_req/{doc_req_id}/file/
# GET the actual file contents of the last submitted candidate for this doc req

12. /lc/{lc_id}/doc_req/{doc_req_id}/autopopulate/

13. /lc/supported_creatable_docs/

14. /lc/supported_creatable_docs/{doc_type}/

"""

urlpatterns = [
    # /lc/{lc_id}/
    url(r'^(?P<lc_id>[0-9]+)/$', views.rud_lc, name='rud_lc'),

    # /lc/by_bank/{bank_id}/
    url(r'^by_bank/(?P<bank_id>[0-9]+)/$', views.cr_lcs, name='cr_lcs'),

    # /lc/by_bank_advisor/{bank_id}/
    url(r'^by_bank_advisor/(?P<bank_id>[0-9]+)/$', views.get_advising, name='get_advising'),

    # /lc/by_bank/{bank_id}/{filter}
    url(r'^by_bank/(?P<bank_id>[0-9]+)/(?P<filter>[\w\-]+)/$', views.get_filtered_lcs, name='get_filtered_lcs'),

    # /lc/by_bank_advisor/{bank_id}/{filter}
    url(r'^by_bank_advisor/(?P<bank_id>[0-9]+)/(?P<filter>[\w\-]+)/$', views.get_filtered_lcs_advisor,
        name='get_filtered_lcs_advisor'),

    # /lc/by_client/{business_id}/
    url(r'^by_client/(?P<business_id>[0-9]+)/$', views.get_lcs_by_client, name='get_lcs_by_client'),

    # /lc/by_beneficiary/{business_id}/
    url(r'^by_beneficiary/(?P<business_id>[0-9]+)/$', views.get_lcs_by_beneficiary, name='get_lcs_by_beneficiary'),

    # /lc/{lc_id}/{state_to_mark}/
    url(r'^(?P<lc_id>[0-9]+)/(?P<state_to_mark>[\w\-]+)/$', views.mark_lc_something, name='mark_lc_something'),

    # /lc/{lc_id}/claim/{relation}/
    url(r'^(?P<lc_id>[0-9]+)/(?P<relation>[\w\-]+)/$', views.claim_relation_to_lc, name='claim_relation_to_lc'),

    # /lc/{lc_id}/doc_req/
    url(r'^(?P<lc_id>[0-9]+)/doc_req/$', views.cr_doc_reqs, name='cr_doc_reqs'),

    # /lc/{lc_id}/doc_req/{doc_req_id}/
    url(r'^(?P<lc_id>[0-9]+)/doc_req/(?P<doc_req_id>[0-9]+)/$', views.rud_doc_req, name='rud_doc_req'),

    # /lc/{lc_id}/doc_req/{doc_req_id}/evaluate/
    url(r'^(?P<lc_id>[0-9]+)/doc_req/(?P<doc_req_id>[0-9]+)/evaluate/$', views.evaluate_doc_req,
        name='evaluate_doc_req'),

    # /lc/{lc_id}/doc_req/{doc_req_id}/file/
    url(r'^(?P<lc_id>[0-9]+)/doc_req/(?P<doc_req_id>[0-9]+)/file/$', views.get_dr_file, name='get_dr_file'),

    # /lc/{lc_id}/doc_req/{doc_req_id}/autopopulate/
    url(r'^(?P<lc_id>[0-9]+)/doc_req/(?P<doc_req_id>[0-9]+)/autopopulate/$', views.autopopulate_creatable_dr,
        name='autopopulate_creatable_dr'),

    # /lc/supported_creatable_docs/
    url(r'^supported_creatable_docs/$', views.supported_creatable_docs, name='supported_creatable_docs'),

    # /lc/supported_creatable_docs/{doc_type}/
    url(r'^supported_creatable_docs/(?P<doc_type>[\w\-]+)/$', views.supported_creatable_doc,
        name='supported_creatable_doc'),

    # /lc/digital_app_templates/
    url(r'^digital_app_templates/$', views.digital_app_templates, name='digital_app_templates'),

    # /lc/digital_app_templates/{template_id}
    url(r'^digital_app_templates/(?P<template_id>[0-9]+)/$', views.digital_app_template, name='digital_app_templates'),

    # /lc/total_credit/{business_id}
    url(r'^total_credit/(?P<business_id>[0-9]+)/$', views.total_credit, name='total_credit'),

    # /lc/check_text_for_boycott
    url(r'^check_text_for_boycott/$', views.check_text_for_boycott, name='check_text_for_boycott'),

    # /lc/check_file_for_boycott
    url(r'^check_file_for_boycott/$', views.check_file_for_boycott, name='check_file_for_boycott'),

    # /lc/clients_by_bank/{bank_id}
    url(r'^clients_by_bank/(?P<bank_id>[0-9]+)/$', views.clients_by_bank, name='clients_by_bank'),

    # /lc/{lc_id}/issuer/select_advising_bank
    url(r'^issuer/(?P<lc_id>[0-9]+)/select_advising_bank', views.issuer_select_advising_bank,
        name='issuer_select_advising_bank')

]
