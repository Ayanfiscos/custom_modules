from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SelectManagerWizard(models.TransientModel):
    _name = 'tender.select_manager.wizard'
    _description = 'Select Manager for Tender Approval'

    manager_id = fields.Many2one('res.users', string='Manager', required=True)

    def action_send_approval_email(self):
        self.ensure_one()
        tender = self.env['tender.tender'].browse(self.env.context.get('active_id'))
        if not tender:
            raise UserError(_('No tender found.'))
        if not self.manager_id.email:
            raise UserError(_('The selected manager does not have an email address.'))
        if not tender.approval_token:
            tender.approval_token = tender._generate_approval_token()
        if tender.state == 'draft':
            tender.state = 'to_approve'
        template = self.env.ref('tender.tender_save_notification_template')
        if template:
            template.email_to = self.manager_id.email
            template.send_mail(tender.id, force_send=True)
            tender.message_post(body=_('Approval request email sent to %s') % self.manager_id.name)
        else:
            raise UserError(_('Email template not found. Please contact your administrator.'))
        return {'type': 'ir.actions.act_window_close'}
