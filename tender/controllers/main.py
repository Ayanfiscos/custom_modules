from odoo import http, _
from odoo.http import request
from werkzeug.exceptions import NotFound
import logging

_logger = logging.getLogger(__name__)

class TenderController(http.Controller):
    @http.route(['/tender/approve/<int:tender_id>/<string:token>'], type='http', auth="public", website=True)
    def approve_tender(self, tender_id, token, **kw):
        # Make sure to get the tender record first
        tender = request.env['tender.tender'].sudo().browse(tender_id)
        
        # Log for debugging purposes using standard Python logger
        _logger.info(f'Approval request received: Tender ID {tender_id}, Token: {token}, Tender exists: {tender.exists()}')
        
        # Check if tender exists
        if not tender.exists():
            return request.render('website.404')
        
        # Check if token is valid
        if token != tender.approval_token:
            return request.render('tender.approval_unauthorized', {
                'tender': tender,
                'message': "Invalid approval token. You are not authorized to approve this tender."
            })
        
        # Check if tender is in the right state
        if tender.state != 'to_approve':
            return request.render('tender.approval_already_processed', {
                'tender': tender,
                'message': "This tender is no longer in 'To Approve' state."
            })
        
        # For public users accessing the link directly from email
        if request.env.user._is_public():
            try:
                # Get the approver information
                approver_name = tender.partner_id.name if tender.partner_id else "Approver"
                approver_email = tender.partner_id.email if tender.partner_id else "Unknown"
                
                # Show the approval/rejection page with buttons
                return request.render('tender.approval_decision', {
                    'tender': tender,
                    'approver_name': approver_name,
                    'token': token
                })
            except Exception as e:
                # Log the error using standard Python logger
                _logger.error(f'Error during tender approval page rendering: {str(e)}')
                
                # Render a generic error page
                return request.render('website.http_error', {
                    'status_code': 500,
                    'status_message': "Internal Server Error"
                })
        else:
            # Logged in user - verify if the current user's email matches the approver's email
            user_email = request.env.user.email
            approver_email = tender.partner_id.email if tender.partner_id else False
            
            if user_email and approver_email and user_email.lower() == approver_email.lower():
                # Show the approval/rejection page with buttons
                return request.render('tender.approval_decision', {
                    'tender': tender,
                    'approver_name': request.env.user.name,
                    'token': token
                })
            else:
                return request.render('tender.approval_unauthorized', {
                    'tender': tender,
                    'message': f"You are not authorized to approve this tender. Only the designated approver ({tender.partner_id.name}) can approve this tender."
                })
    
    @http.route(['/tender/process/<int:tender_id>/<string:token>/<string:action>'], type='http', auth="public", website=True)
    def process_tender_decision(self, tender_id, token, action, **kw):
        # Make sure to get the tender record first
        tender = request.env['tender.tender'].sudo().browse(tender_id)
        
        # Log for debugging purposes
        _logger.info(f'Processing tender decision: ID {tender_id}, Token: {token}, Action: {action}')
        
        # Check if tender exists
        if not tender.exists():
            return request.render('website.404')
        
        # Check if token is valid
        if token != tender.approval_token:
            return request.render('tender.approval_unauthorized', {
                'tender': tender,
                'message': "Invalid approval token. You are not authorized to approve or reject this tender."
            })
        
        # Check if tender is in the right state
        if tender.state != 'to_approve':
            return request.render('tender.approval_already_processed', {
                'tender': tender,
                'message': "This tender is no longer in 'To Approve' state."
            })
        
        # Get approver info
        if request.env.user._is_public():
            approver_name = tender.partner_id.name if tender.partner_id else "Approver"
            approver_email = tender.partner_id.email if tender.partner_id else "Unknown"
        else:
            approver_name = request.env.user.name
            approver_email = request.env.user.email
        
        try:
            if action == 'approve':
                # Approve the tender
                tender.sudo().action_approve()
                
                # Record who approved it
                tender.sudo().message_post(
                    body=f"Tender was approved via email link by {approver_name} ({approver_email})",
                    subtype_xmlid="mail.mt_note"
                )
                
                # Show confirmation page
                return request.render('tender.approval_success', {
                    'tender': tender,
                    'approver_name': approver_name
                })
            
            elif action == 'reject':
                # Reject the tender
                tender.sudo().action_reject()
                
                # Record who rejected it
                tender.sudo().message_post(
                    body=f"Tender was rejected via email link by {approver_name} ({approver_email})",
                    subtype_xmlid="mail.mt_note"
                )
                
                # Show rejection confirmation page
                return request.render('tender.rejection_success', {
                    'tender': tender,
                    'approver_name': approver_name
                })
            
            else:
                # Invalid action
                return request.render('tender.approval_error', {
                    'tender': tender,
                    'error_message': "Invalid action. Please use either 'approve' or 'reject'."
                })
                
        except Exception as e:
            # Log the error
            _logger.error(f'Error processing tender decision: {str(e)}')
            
            # Render a generic error page
            return request.render('website.http_error', {
                'status_code': 500,
                'status_message': "Internal Server Error"
            })