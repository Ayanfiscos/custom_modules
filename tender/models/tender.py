from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from odoo.exceptions import ValidationError
from datetime import timedelta
import re

_logger = logging.getLogger(__name__)

class Tender(models.Model):
    _name = "tender.tender"
    _description = "Tender"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Tender Title', required=True, tracking=True)
    tender_reference = fields.Char(string='Tender Reference Number', required=True, tracking=True)
    company_name = fields.Char(string='Company Name', required=True, tracking=True)
    date_receipt = fields.Date(string='Date of Receipt', required=True, tracking=True)
    date_submission = fields.Date(string='Date of Submission', required=True, tracking=True)
    manager_id = fields.Many2one('res.users', string="Manager", required=True, tracking=True)
    is_converted_to_contract = fields.Boolean(string="Converted to Contract", default=False, tracking=True)
    partner_id = fields.Many2one('res.partner', string="Partner", tracking=True)
    tender_type = fields.Selection([
        ('open', 'Open Tender'),
        ('selective', 'Selective Tender'),
        ('negotiated', 'Negotiated Tender'),
        ('limited', 'Limited Tender'),
        ('request_for_proposal', 'Request for Proposal (RFP)'),
        ('request_for_quotation', 'Request for Quotation (RFQ)'),
        ('other', 'Other')
    ], string='Type of Tender', required=True, tracking=True)
    tender_category = fields.Selection([
        ('goods', 'Goods'),
        ('services', 'Services'),
        ('works', 'Works'),
        ('consultancy', 'Consultancy'),
        ('other', 'Other')
    ], string='Category of Tender', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve', 'To Approve'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('submitted', 'Submitted to Client'),
        ('inspection', 'Inspection'),
        ('pending_information', 'Pending Information'),
        ('won', 'won'),
        ('lost', 'lost'),
    ], string='Status', default='draft', tracking=True, copy=False)
    tender_outcome = fields.Selection([
        ('pending', 'Pending'),
        ('won', 'Won'),
        ('lost', 'Lost'),
    ], string='Tender Outcome', tracking=True, default='pending', copy=False)
    
    phone = fields.Char(string="Tender Contact's Number", tracking=True)
    
    @api.constrains('phone')
    def _check_phone_number(self):
        for record in self:
            if record.phone:
                # Remove spaces and special characters for comparison
                phone_pattern = re.compile(r'^\+?[0-9]{10,15}$')
                phone_number = re.sub(r'\s+|-|\(|\)', '', record.phone)
                if not phone_pattern.match(phone_number):
                    raise ValidationError(_("Invalid phone number format. Please enter a valid phone number."))

    def action_save_record(self):
        """ Save the tender record """
        self.ensure_one()
        _logger.info(f"Tender {self.name} saved.")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Tender saved successfully.'),
                'sticky': False,
                'type': 'success',
            }
        }

    def action_send_email(self):
        """ Send the email and move to 'To Approve' stage """
        try:
            template = self.env.ref('tender.tender_save_notification_template')
            _logger.info(f"Manager ID: {self.manager_id}, Email: {self.manager_id.email if self.manager_id else 'None'}")
            if not self.manager_id or not self.manager_id.email:
                fallback_email = self.env.user.email
                if not fallback_email:
                    raise UserError(_("No manager email or fallback user email configured. Please set a manager or user email."))
                _logger.warning(f"Using fallback email {fallback_email} for Tender {self.name}.")
            template.send_mail(self.id, force_send=True)
            self.write({'state': 'to_approve'})
            _logger.info(f"Email sent for Tender {self.name} to {self.manager_id.email or fallback_email}.")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Email sent successfully. Tender moved to "To Approve" stage.'),
                    'sticky': False,
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error(f"Failed to send email for Tender {self.name}: {e}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': str(e),
                    'sticky': True,
                    'type': 'danger',
                }
            }

    def action_approve(self):
        for record in self:
            if record.state != 'to_approve':
                raise UserError("Tender must be in 'To Approve' state to be approved.")
            record.state = 'approved'

    def action_reject(self):
        for record in self:
            if record.state != 'to_approve':
                raise UserError("Tender must be in 'To Approve' state to be rejected.")
            record.state = 'rejected'

    def action_submit_to_client(self):
        for record in self:
            if record.state != 'approved':
                raise UserError("Tender must be in 'Approved' state to be submitted to client.")
            record.state = 'submitted'

    def action_request_inspection(self):
        for record in self:
            if record.state != 'submitted':
                raise UserError("Tender must be in 'Submitted' state to request inspection.")
            record.state = 'inspection'

    def action_mark_pending_info(self):
        for record in self:
            if record.state not in ['submitted', 'inspection']:
                raise UserError("Pending info can only come after submission or inspection.")
            record.state = 'pending_information'

    def action_mark_won(self):
        for record in self:
            if record.state not in ['pending_information', 'submitted', 'inspection']:
                raise UserError("You can only mark as won after client feedback.")
            record.state = 'won'
            record.tender_outcome = 'won'

            # Automatically create a contract when the tender is marked as won
            start_date = fields.Date.today()
            end_date = start_date + timedelta(days=365)  # Setting end date one year from start date

            contract = self.env['tender.contract'].create({
                'name': f"Contract for {record.name}",
                'company_name': record.company_name,
                'tender_id': record.id,
                'contract_reference': record.tender_reference,
                'start_date': start_date,
                'end_date': end_date,
                'tender_outcome': record.tender_outcome,
                'approved_amount': 0.0,
            })
            record.is_converted_to_contract = True
            record.message_post(
                body=f"Contract '{contract.name}' has been automatically created upon marking the tender as won.",
                subtype_xmlid="mail.mt_note"
            )

    def action_mark_lost(self):
        for record in self:
            record.state = 'lost'
            record.tender_outcome = 'lost'

    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'

    def action_convert_to_contract(self):
        for record in self:
            if record.state != 'won':
                raise UserError("Only won tenders can be converted to contracts.")
            self.env['tender.contract'].create({
                'name': f"Contract for {record.name}",
                'company_name': record.company_name,
                'tender_id': record.id,
                'contract_reference': record.tender_reference,
                'start_date': fields.Date.today(),
                'approved_amount': 0.0,
            })
            record.is_converted_to_contract = True