from django.conf.urls import url
from . import views

""" Endpoints:
1. /lc/{bank_id}
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
        'lc_id' : an integer of the ID of your lc
    }
    # If its a BankEmployee POSTing, we expect
    [app_response_that_i_uploaded_on_behalf_of_a_client.pdf]
    or, for creating an LC app that your client will fill out later (which bountium will notify them about)
    {
        'applicant' : 'the applicants business name',
        'applicant_employee_contact' : 'someemployee@business.com'
        [we'll either create the Business in our database, or re-use if this is a repeat]
    }

2. /lc/{lc_id} (a very busy endpoint lol)
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
# TODO this handles redlining - how are we going to save the history of redlined changes to render back to the user?
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

3. /lc/{lc_id}/evaluate
# POST the following to approve of an LC, or disapprove with attached complaints during redlining, as either an employee of
    (<lc for which id == lc_id>.issuer)
or
    (<lc for which id == lc_id>.beneficiary)
{
    'approve': true || false,
    'complaints' : 'any complaints; blank if approve == true'
}

4. /lc/{lc_id}/notify
# POST the following
{
    'to_notify' : 'email_of_teammate@issuingbank.com',
    'note' : 'optionally, send a note with the request'
}
# as a currently assigned BankEmployee of the issuing bank to notify a teammate of some need on the LC. If the teammate is not yet assigned to this LC, this will assign them to it.

5. /lc/{lc_id}/doc_req
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

6. /lc/{lc_id}/doc_req/{doc_req_id}
# GET a doc req, whether or not a doc has been submitted yet
# PUT a number of options:
- as the beneficiary
{
    'link_to_submitted_doc' : https://somecloudhost.com/link_to_the/file.pdf
}
to submit a candidate for this doc req, notifying the issuer of this change and reverting the doc reqs status to unapproved. Receive back
{
    'success':true || false,
    'modified_and_notified_on':str(datetime.datetime.now()),
    'doc_req':{the new doc_req's data and status}
}
- as the issuer, any subset of the following fields
{
    'due_date':int of the unix time of the new due date,
    'required_values':'a new required values str'
}
to update the terms of this doc req, notifying the beneficiary and client. If new due_date !> old due_date, or new required_values !== old required_values, the lc will be marked as modified_and_awaiting_beneficiary_approval. Receive back
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

7. /lc/{lc_id}/doc_req/{doc_req_id}/evaluate
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

8. /lc/{lc_id}/request
# POST as an employee of the beneficiary to request payment

9. /lc/{lc_id}/draw
# POST as an employee of the beneficiary to demand a draw on the LC

10. /lc/{lc_id}/payout
# POST as an employee of the client or bank to mark an LC as paid out

"""

urlpatterns = [
    # /lc/{bank_id}
    url(r'^(?P<bank_id>[0-9]+)/$', views.cr_lcs, name='cr_lcs'),

    # /lc/{lc_id}
    url(r'^(?P<lc_id>[0-9]+)/$', views.rud_lc, name='rud_lc'),

    # /lc/{lc_id}/evaluate
    url(r'^(?P<lc_id>[0-9]+)/evaluate/$', views.evaluate_lc, name='evaluate_lc'),

    # /lc/{lc_id}/notify
    url(r'^(?P<lc_id>[0-9]+)/notify/$', views.notify_teammate, name='notify_teammate'),

    # /lc/{lc_id}/doc_req
    url(r'^(?P<lc_id>[0-9]+)/doc_req/$', views.cr_doc_reqs, name='cr_doc_reqs'),

    # /lc/{lc_id}/doc_req/{doc_req_id}
    url(r'^(?P<lc_id>[0-9]+)/doc_req/(?P<doc_req_id>[0-9]+)$', views.rud_doc_req, name='rud_doc_req'),

    # /lc/{lc_id}/doc_req/{doc_req_id}/evaluate
    url(r'^(?P<lc_id>[0-9]+)/doc_req/(?P<doc_req_id>[0-9]+)$', views.evaluate_doc_req, name='evaluate_doc_req'),

    # /lc/{lc_id}/request
    url(r'^(?P<lc_id>[0-9]+)/request/$', views.request_lc, name='request_lc'),

    # /lc/{lc_id}/draw
    url(r'^(?P<lc_id>[0-9]+)/draw/$', views.draw_lc, name='draw_lc'),

    # /lc/{lc_id}/payout
    url(r'^(?P<lc_id>[0-9]+)/payout/$', views.payout_lc, name='payout_lc'),

]
