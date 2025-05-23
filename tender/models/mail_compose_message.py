# my_tender_module/models/mail_compose_message.py
from odoo import models, _
from odoo.exceptions import UserError

class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def action_send_mail(self):
        # Check if there are any recipients
        if not self.partner_ids:
            raise UserError(_('Please select at least one recipient before sending the email.'))
        tender_id = self.env.context.get('default_res_ids', [False])[0]
        if tender_id and self.env.context.get('default_model') == 'tender.tender':
            # Update the tender's state to 'submitted'
            tender = self.env['tender.tender'].browse(tender_id)
            tender.write({'state': 'submitted'})
            
        # If recipients exist, proceed with the original send action
        return super(MailComposeMessage, self).action_send_mail()