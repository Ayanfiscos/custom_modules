from odoo import http, _
from odoo.http import request
from werkzeug.exceptions import NotFound
import logging

_logger = logging.getLogger(__name__)

class TenderController(http.Controller):
    @http.route(['/tender/approve/<int:tender_id>/<string:token>'], type='http', auth="public", website=True)
    def approve_tender(self, tender_id, token, **kw):
        tender = request.env['tender.tender'].sudo().browse(tender_id)
        _logger.info(f'Approval request received: Tender ID {tender_id}, Token: {token}, Tender exists: {tender.exists()}')

        if not tender.exists():
            return request.render('website.404')

        if token != tender.approval_token:
            return request.render('tender.approval_unauthorized', {
                'tender': tender,
                'message': "Invalid approval token. You are not authorized to approve this tender."
            })

        if tender.state != 'to_approve':
            return request.render('tender.approval_already_processed', {
                'tender': tender,
                'message': "This tender is no longer in 'To Approve' state."
            })

        # For public users accessing the link directly from email
        if request.env.user._is_public():
            try:
                return request.render('tender.approval_decision', {
                    'tender': tender,
                    'approver_name': "Sales / Administrator",
                    'token': token
                })
            except Exception as e:
                _logger.error(f'Error during tender approval page rendering: {str(e)}')
                return request.render('website.http_error', {
                    'status_code': 500,
                    'status_message': "Internal Server Error"
                })
        else:
            # Allow any user in Sales / Administrator group to approve
            if request.env.user.has_group('sales_team.group_sale_manager'):
                return request.render('tender.approval_decision', {
                    'tender': tender,
                    'approver_name': request.env.user.name,
                    'token': token
                })
            else:
                return request.render('tender.approval_unauthorized', {
                    'tender': tender,
                    'message': "You are not authorized to approve this tender. Only Sales / Administrator group members can approve."
                })

    @http.route(['/tender/process/<int:tender_id>/<string:token>/<string:action>'], type='http', auth="public", website=True)
    def process_tender_decision(self, tender_id, token, action, **kw):
        tender = request.env['tender.tender'].sudo().browse(tender_id)
        _logger.info(f'Processing tender decision: ID {tender_id}, Token: {token}, Action: {action}')

        if not tender.exists():
            return request.render('website.404')

        if token != tender.approval_token:
            return request.render('tender.approval_unauthorized', {
                'tender': tender,
                'message': "Invalid approval token. You are not authorized to approve or reject this tender."
            })

        if tender.state != 'to_approve':
            return request.render('tender.approval_already_processed', {
                'tender': tender,
                'message': "This tender is no longer in 'To Approve' state."
            })

        # Get approver info
        if request.env.user._is_public():
            approver_name = "Sales / Administrator"
            approver_email = "N/A"
        else:
            approver_name = request.env.user.name
            approver_email = request.env.user.email

        # Only allow group members to process
        if not request.env.user._is_public() and not request.env.user.has_group('sales_team.group_sale_manager'):
            return request.render('tender.approval_unauthorized', {
                'tender': tender,
                'message': "You are not authorized to approve or reject this tender. Only Sales / Administrator group members can do this."
            })

        try:
            if action == 'approve':
                tender.sudo().action_approve()
                tender.sudo().message_post(
                    body=f"Tender was approved via email link by {approver_name} ({approver_email})",
                    subtype_xmlid="mail.mt_note"
                )
                return request.render('tender.approval_success', {
                    'tender': tender,
                    'approver_name': approver_name
                })

            elif action == 'reject':
                tender.sudo().action_reject()
                tender.sudo().message_post(
                    body=f"Tender was rejected via email link by {approver_name} ({approver_email})",
                    subtype_xmlid="mail.mt_note"
                )
                return request.render('tender.rejection_success', {
                    'tender': tender,
                    'approver_name': approver_name
                })

            else:
                return request.render('tender.approval_error', {
                    'tender': tender,
                    'error_message': "Invalid action. Please use either 'approve' or 'reject'."
                })

        except Exception as e:
            _logger.error(f'Error processing tender decision: {str(e)}')
            return request.render('website.http_error', {
                'status_code': 500,
                'status_message': "Internal Server Error"
            })