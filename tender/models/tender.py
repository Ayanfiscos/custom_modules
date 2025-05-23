from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from odoo.exceptions import ValidationError
from datetime import timedelta
import re
import uuid
import werkzeug.urls

_logger = logging.getLogger(__name__)

class Tender(models.Model):
    _name = "tender.tender"
    _description = "Tender"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Tender Title', required=True, tracking=True)
    tender_number = fields.Char(string='Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: self._get_default_reference(),)
    tender_reference = fields.Char(string='Tender Reference Number', required=True, tracking=True)
    company_name = fields.Char(string='Company Name', required=True, tracking=True)
    date_receipt = fields.Date(string='Date of Receipt', required=True, tracking=True)
    date_submission = fields.Date(string='Date of Submission', required=True, tracking=True)
    is_converted_to_contract = fields.Boolean(string="Converted to Contract", default=False, tracking=True)
    additional_note = fields.Text(string='Additional Note', tracking=True)
    partner_id = fields.Many2one('res.partner', string="Approver", tracking=True, 
                                help="Select the partner who will receive the approval email")
    manager_id = fields.Many2one('res.groups', string='Manager', tracking=True, help='The manager responsible for approving this tender.')
    contract_id = fields.Many2one('tender.contract', string='Contract', tracking=True)
    tender_type = fields.Selection([
        ('single tender', 'Single Tender'),
        ('double tender', 'Double Tender'),
    ], string='Type of Tender', required=True, tracking=True)
    # tender_category = fields.Selection([
    #     ('goods', 'Goods'),
    #     ('services', 'Services'),
    #     ('works', 'Works'),
    #     ('consultancy', 'Consultancy'),
    #     ('other', 'Other')
    # ], string='Category of Tender', required=True, tracking=True)
    status= fields.Selection([
        ('Awarded', 'Awarded'),
        ('Not Awarded', 'Not Awarded'),
        ('Pending', 'Pending'),
    ], string='Status', default='Pending', tracking=True)
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
    ], string='State', default='draft', tracking=True, copy=False)
    tender_outcome = fields.Selection([
        ('pending', 'Pending'),
        ('won', 'Won'),
        ('rejected', 'Rejected'),
        ('lost', 'Lost'),
    ], string='Tender Outcome', tracking=True, default='pending', copy=False)
    
    contact_name = fields.Char(string="Tender Contact's Name", tracking=True, required=True)
    approval_token = fields.Char(string='Approval Token', copy=False)
    evaluation_contract_status = fields.Selection([
        ('evaluation', 'Evaluation'),
        ('contract_awarded', 'Awarded'),
    ], string='Evaluation / Contract Award', default='evaluation', tracking=True)
    additional_note = fields.Text(string='Additional Note')

    request_inspection = fields.Boolean(
        string="Request Inspection",
        default=False,
        tracking=True,
    )

    _sql_constraints = [
        ('tender_reference_unique', 'unique(tender_reference)', 'The Tender Reference Number must be unique!'),
        ('company_name_title_unique', 'unique(company_name, name)', 'A company cannot have two tenders with the same project title!'),
    ]

    def _generate_approval_token(self):
        """Generate a random token for tender approval."""
        return str(uuid.uuid4())

    def get_approval_url(self):
        """Get the URL for tender approval."""
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        
        # Generate a token if not already created
        if not self.approval_token:
            self.approval_token = self._generate_approval_token()
        
        return f"{base_url}/tender/approve/{self.id}/{self.approval_token}"
    
    def action_submit_to_client(self):
        self.ensure_one()

        if self.state != 'approved':
            raise UserError("Tender must be in 'Approved' state to be submitted to client.")
        
        # Generate the PDF report
        import base64
        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf('tender.action_report_tender', [self.id])
        attachment_vals = {
            'name': f"Tender - {self.name}.pdf",
            'type': 'binary',
            'datas': base64.b64encode(pdf_content).decode('utf-8'),
            'res_model': 'tender.tender',
            'res_id': self.id,
        }
        attachment = self.env['ir.attachment'].create(attachment_vals)
        
        template = self.env.ref('tender.tender_email_template')
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = {
            'default_model': 'tender.tender',
            'default_res_ids': [self.id],
            'default_use_template': bool(template),
            'default_template_id': template.id if template else False,
            'default_composition_mode': 'comment',
            'mark_tender_as_sent': True,
            # 'default_attachment_ids': [(6, 0, [attachment.id])],  # Ensure PDF is attached
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    def action_send_email(self):
        """Send approval email to the selected partner."""
        self.ensure_one()
        # Ensure a partner is selected before sending email
        group = self.env.ref('sales_team.group_sale_manager')
        users = group.users
        emails = [user.email for user in users if user.email]
        if not emails:
            raise UserError(_("No email address found for the selected approver. Please update the approver's email address."))
        # # Check if partner is selected
        # if not self.manager_id:
        #     raise UserError(_("Please select an approver for this tender."))
        
        # # Check if partner has an email
        # if not self.manager_id.email:
        #     raise UserError(_("The selected approver doesn't have an email address. Please update the partner's email or select another approver."))
        
        # Generate approval token if not already created
        if not self.approval_token:
            self.approval_token = self._generate_approval_token()
        
        # Change state to 'to_approve'
        if self.state == 'draft':
            self.state = 'to_approve'
        
        # Send email using template
        template = self.env.ref('tender.tender_save_notification_template')
        if template:
            for email in emails:
                template.sudo().send_mail(self.id, email_values={'email_to': email}, force_send=True)
            self.message_post(body=_("Approval request email sent to %s") % self.partner_id.name)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Email Sent'),
                    'message': _('Approval request has been sent to %s') % self.partner_id.name,
                    'sticky': False,
                    'type': 'success',
                }
            }
        else:
            raise UserError(_("Email template not found. Please contact your administrator."))
        
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
        
    def action_approve(self):
        self.ensure_one()
        if not self.env.user.has_group('sales_team.group_sale_manager'):
            raise UserError(_("Only Sales / Administrator group members can approve this tender."))
        if self.state != 'to_approve':
            raise UserError(_("tender is not in a state that can be approved."))
        self.state = 'approved'
        self.message_post(body=_("Tender has been approved by %s") % self.env.user.name)
        
    def action_reject(self):
        self.ensure_one()
        if not self.env.user.has_group('sales_team.group_sale_manager'):
            raise UserError(_("Only Sales / Administrator group members can reject this tender."))
        if self.state != 'to_approve':
            raise UserError(_("tender is not in a state that can be rejected."))
        self.state = 'rejected'
        self.message_post(body=_("Tender has been rejected by %s") % self.env.user.name)
        self.tender_outcome = 'rejected'

    def action_reset(self):
        for record in self:
            record.state = 'draft'

    def action_request_inspection(self):
        for record in self:
            record.request_inspection = True
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
            record.status = 'Awarded'

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
            _logger.info(f"Created contract {contract.id} for tender {record.id}")
            record.contract_id = contract  # Link the contract to the tender
            _logger.info(f"Tender {record.id} now has contract_id {record.contract_id.id}")
            record.is_converted_to_contract = True
            record.message_post(
                body=f"Contract '{contract.name}' has been automatically created upon marking the tender as won.",
                subtype_xmlid="mail.mt_note"
            )

    def action_open_related_contract(self):
        self.ensure_one()  # Ensure we're working with a single record
        if not self.contract_id:
            raise UserError("There is no contract for this tender.")
        # Return the action to open the existing contract
        return {
            'type': 'ir.actions.act_window',
            'name': 'Open Contract',
            'res_model': 'tender.contract',
            'view_mode': 'form',
            'res_id': self.contract_id.id,  # Open the specific contract
            'target': 'current',
        }
    
    def action_mark_lost(self):
        for record in self:
            record.state = 'lost'
            record.tender_outcome = 'lost'
            record.status = 'Not Awarded'

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


    user_has_group = fields.Boolean(
        compute="_compute_user_has_group", 
        string="User Has Group", 
        store=False
    )

    def _compute_user_has_group(self):
        for rec in self:
            rec.user_has_group = self.env.user.has_group('sales_team.group_sale_manager')

    @api.model
    def _get_default_reference(self):
        return self.env['ir.sequence'].next_by_code('tender.tender') or 'New'
    # def create(self, vals):
    #     if vals.get('tender_number', 'New') or vals['tender_number'] == 'New':
    #         vals['tender_number'] = self.env['ir.sequence'].next_by_code('tender.tender') or 'New'
    #     return super(Tender, self).create(vals)

    @api.onchange('request_inspection')
    def _onchange_request_inspection(self):
        for rec in self:
            if rec.state == 'submitted' and rec.request_inspection:
                rec.state = 'inspection'
                # rec.request_inspection = False  # Do NOT reset the toggle

    def action_awaiting_result(self):
        if self.state not in ['submitted', 'inspection']:
            raise UserError("Tender must be in 'Submitted to Client or Inspection' state to await result.")
        if self.state == 'inspection':
            self.state = 'pending_information'
        elif self.request_inspection:
            self.state = 'inspection'
        else:
            self.state = 'pending_information'

    # @api.model
    # def create(self, vals):
    #     tender = super(Tender, self).create(vals)
    #     if tender.state == 'won':
    #         tender._populate_other_info_and_contract()
    #     return tender

    # def write(self, vals):
    #     res = super(Tender, self).write(vals)
    #     if 'state' in vals and vals['state'] == 'won':
    #         self._populate_other_info_and_contract()
    #     return res

    # def _populate_other_info_and_contract(self):
    #     for record in self:
    #         # Populate Other Information
    #         record.other_info_ids.create({
    #             'tender_id': record.id,
    #             'additional_note': f"Auto-generated for {record.name}",
    #             'contact_name': record.contact_name,
    #         })

            # Populate Contract Lines
            # record.contract_line_ids.create({
            #     'tender_id': record.id,
            #     'name': f"Contract for {record.name}",
            #     'tender_type': record.tender_type,
            #     'state': 'won',
            #     'date_receipt': record.date_receipt,
            #     'date_submission': record.date_submission,
            #     'company_name': record.company_name,
            # })
    def action_view_tenders(self):
        # Return action to open related receipts
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tenders',
            'res_model': 'tender.tender',
            'view_mode': 'tree,form',
            'domain': [('tender_id', '=', self.id)],
            'target': 'current',
        }