from django.conf.urls import url
from . import views

""" Endpoints:
1. /lc/{bank_id}
# GET all the lcs from this bank (TODO: thats probably just for testing)
# POST the following to create an LC at this bank
    # If its a BusinessEmployee POSTing, we expect one of
    <aFilledOutPDFApp.pdf>
    or, a JSON arr of LCApplicationQuestionResponses
    [
        {
            'for_question' : int of the questions id,
            'user_response' : <the user's response as a json string or int or whatever>
        }
    ]
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

2. /lc/{bank_id}/{lc_id} (a very busy endpoint lol)
# POST to respond to a created LC application
    # If
        !(<lc for which id == lc_id>.filledOut)
        && (<the employee POSTing>.employer == <lc for which id == lc_id>.applicant)
    we expect this to be the rest of the values required to create an LC - one of:
    <aFilledOutPDFApp.pdf>
    or, a JSON arr of LCApplicationQuestionResponses
    [
        {
            'for_question' : int of the questions id,
            'user_response' : <the user's response as a json string or int or whatever>
        }
    ]
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
    'other_responses' : [
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
- you are the applicant or issuing bank, and the LC is not (beneficiary_approved && issuer_approved)

3. /lc/{lc_id}/approve
# POST to approve an LC during redlining, as either an employee of
    (<lc for which id == lc_id>.issuer)
or
    (<lc for which id == lc_id>.beneficiary)

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
    'submitted_doc' : [the submitted doc.pdf],
    'for_doc_req' : optional, the int of the doc req this is for. this only applies to DigitalLCs
}
as an employee of the beneficiary to submit a DocumentaryRequirement
    if its for a PdfLC we'll be creating the DocumentaryRequirement
    if its for a DigitalLC we'll be updating the DocumentaryRequirement

6. /lc/{lc_id}/doc_req/{doc_req_id}
POST the following
{
    'approve': true || false,
    'complaints' : 'any complaints; blank if approve == true'
}
as an employee of the issuing bank or client to approve/dispute a DocumentaryRequirement
# GET a doc req, whether or not a doc has been submitted yet

7. /lc/{lc_id}/request
# POST as an employee of the beneficiary to request payment

8. /lc/{lc_id}/draw
# POST as an employee of the beneficiary to demand a draw on the LC

9. /lc/{lc_id}/payout
# POST as an employee of the client or bank to mark an LC as paid out

"""

urlpatterns = [
    # /lc/
    url(r'^$', views.index, name='index')

]
