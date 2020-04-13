from django.conf.urls import url
from . import views

""" Endpoints:
1. /lc/by_bank/{bank_id}/
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

2. /lc/{lc_id}/ (a very busy endpoint lol)
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
Note that an unsuccessful delete attempt is different from a bad request, forbidden, request, or 404. Its a *valid* request in the software, but a request we cannot honor in implementation.

3. /lc/by_bank/{bank_id}/live/
# GET, and receive back a list of LCs that are
- issued by the bank with id=bank_id
- approved by all parties
- not yet paid out

4. /lc/by_bank/{bank_id}/awaiting_issuer_approval/
# GET, and receive back a list of LCs that are
- issued (or requested to be issued via using their bountium-hosted application) by the bank with id=bank_id
- not yet approved by the issuer

5. /lc/by_bank/{bank_id}/awaiting_beneficiary_approval/
# GET, and receive back a list of LCs that are
- issued by the bank with id=bank_id
- not yet approved by the beneficiary

6. /lc/by_bank/{bank_id}/awaiting_client_approval/
# GET, and receive back a list of LCs that are
- issued by the bank with id=bank_id
- not yet approved by the client

7. /lc/by_client/{business_id}/
# GET, and receive back a list of LCs that are
- credited from (or, if not yet approved, applied from) the business for which id=business_id

8. /lc/by_beneficiary/{business_id}/
# GET, and receive back a list of LCs that are
- credited to (or, if not yet approved, proposed-to-be-credited-to) the business for which id=business_id

9. /lc/{lc_id}/notify/
# POST the following
{
    'to_notify' : 'email_of_teammate@issuingbank.com',
    'note' : 'optionally, send a note with the request'
}
# as an employee of the issuer, client, or beneficiary,
# to notify a teammate of some need on the LC.
# If the teammate is not yet assigned to this LC, this will assign them to it.

10. /lc/{lc_id}/claim_beneficiary/
# POST as a logged-in BusinessEmployee to claim beneficiary status on this lc

11. /lc/{lc_id}/claim_account_party/
# POST as a logged-in BusinessEmployee to claim account party status on this lc

12. /lc/{lc_id}/claim_advising/
# POST as a logged-in BankEmployee to claim advising bank status on this lc

13. /lc/{lc_id}/evaluate/
# POST the following to approve of an LC, or disapprove with attached complaints during redlining, as either an employee of
    (<lc for which id == lc_id>.issuer)
or
    (<lc for which id == lc_id>.beneficiary)
{
    'approve': true || false,
    'complaints' : 'any complaints; blank if approve == true'
}

14. /lc/{lc_id}/doc_req/
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
    if its for a DigitalLC we'll be adding this as an auxiliary DocumentaryRequirement, and return a JSON response with its ID:
        {
            'doc_req_id' : int of the doc reqs id
        }
    NOTE: If you are submitting a doc req for an existing doc req you should PUT to /lc/{lc_id}/doc_req/{doc_req_id}
# GET the current doc reqs and statuses

15. /lc/{lc_id}/doc_req/{doc_req_id}/
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

16. /lc/{lc_id}/doc_req/{doc_req_id}/evaluate/
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
- as an employee of the beneficiary to approve/dispute any modifications made by the issuer to this doc req, if doc_req.modified_and_awaiting_beneficiary_approval, with
{
    'approve': true || false,
    'complaints' : 'any complaints; blank if approve == true'
}
and receive back
{
    'success': true || false,
    'doc_reqs':[{list of resultant doc reqs and their statuses}]
}

17. /lc/{lc_id}/request/
# POST as an employee of the beneficiary to request payment

18. /lc/{lc_id}/draw/
# POST as an employee of the beneficiary to demand a draw on the LC

19. /lc/{lc_id}/payout/
# POST as an employee of the client or bank to mark an LC as paid out

20. /lc/{lc_id}/doc_req/{doc_req_id}/file/
# GET the actual file contents of the last submitted candidate for this doc req

"""

urlpatterns = [
    # /lc/by_bank/{bank_id}/
    url(r'^by_bank/(?P<bank_id>[0-9]+)/$', views.cr_lcs, name='cr_lcs'),

    # /lc/{lc_id}/
    url(r'^(?P<lc_id>[0-9]+)/$', views.rud_lc, name='rud_lc'),

    # /lc/by_bank/{bank_id}/live/
    url(r'^by_bank/(?P<bank_id>[0-9]+)/live/$', views.get_live_lcs, name='get_live_lcs'),

    # /lc/by_bank/{bank_id}/awaiting_issuer_approval/
    url(r'^by_bank/(?P<bank_id>[0-9]+)/awaiting_issuer_approval/$', views.get_lcs_awaiting_issuer, name='get_lcs_awaiting_issuer'),

    # /lc/by_bank/{bank_id}/awaiting_beneficiary_approval/
    url(r'^by_bank/(?P<bank_id>[0-9]+)/awaiting_beneficiary_approval/$', views.get_lcs_awaiting_beneficiary, name='get_lcs_awaiting_beneficiary'),

    # /lc/by_bank/{bank_id}/awaiting_client_approval/
    url(r'^by_bank/(?P<bank_id>[0-9]+)/awaiting_client_approval/$', views.get_lcs_awaiting_client, name='get_lcs_awaiting_client'),

    # /lc/by_client/{business_id}/
    url(r'^by_client/(?P<business_id>[0-9]+)/$', views.get_lcs_by_client, name='get_lcs_by_client'),

    # /lc/by_beneficiary/{business_id}/
    url(r'^by_beneficiary/(?P<business_id>[0-9]+)/$', views.get_lcs_by_beneficiary, name='get_lcs_by_beneficiary'),

    # /lc/{lc_id}/notify/
    url(r'^(?P<lc_id>[0-9]+)/notify/$', views.notify_teammate, name='notify_teammate'),

    # /lc/{lc_id}/claim_beneficiary/
    url(r'^(?P<lc_id>[0-9]+)/claim_beneficiary/$', views.claim_beneficiary, name='claim_beneficiary'),

    # /lc/{lc_id}/claim_account_party/
    url(r'^(?P<lc_id>[0-9]+)/claim_account_party/$', views.claim_account_party, name='claim_account_party'),

    # /lc/{lc_id}/claim_advising/
    url(r'^(?P<lc_id>[0-9]+)/claim_advising/$', views.claim_advising, name='claim_advising'),

    # /lc/{lc_id}/evaluate/
    url(r'^(?P<lc_id>[0-9]+)/evaluate/$', views.evaluate_lc, name='evaluate_lc'),

    # /lc/{lc_id}/doc_req/
    url(r'^(?P<lc_id>[0-9]+)/doc_req/$', views.cr_doc_reqs, name='cr_doc_reqs'),

    # /lc/{lc_id}/doc_req/{doc_req_id}/
    url(r'^(?P<lc_id>[0-9]+)/doc_req/(?P<doc_req_id>[0-9]+)/$', views.rud_doc_req, name='rud_doc_req'),

    # /lc/{lc_id}/doc_req/{doc_req_id}/evaluate/
    url(r'^(?P<lc_id>[0-9]+)/doc_req/(?P<doc_req_id>[0-9]+)/evaluate/$', views.evaluate_doc_req, name='evaluate_doc_req'),

    # /lc/{lc_id}/request/
    url(r'^(?P<lc_id>[0-9]+)/request/$', views.request_lc, name='request_lc'),

    # /lc/{lc_id}/draw/
    url(r'^(?P<lc_id>[0-9]+)/draw/$', views.draw_lc, name='draw_lc'),

    # /lc/{lc_id}/payout/
    url(r'^(?P<lc_id>[0-9]+)/payout/$', views.payout_lc, name='payout_lc'),

    # /lc/{lc_id}/doc_req/{doc_req_id}/file/
    url(r'^(?P<lc_id>[0-9]+)/doc_req/(?P<doc_req_id>[0-9]+)/file/$', views.get_dr_file, name='get_dr_file'),

]
