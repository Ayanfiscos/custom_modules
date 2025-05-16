from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ExtendDeadlineWizard(models.TransientModel):
    _name = 'tender.extend_deadline.wizard'
    _description = 'Extend Tender Submission Deadline'

    new_date_submission = fields.Date(string='New Submission Deadline', required=True)
    reason = fields.Text(string='Reason for Extension', required=True)

    def action_extend_deadline(self):
        self.ensure_one()
        tender = self.env['tender.tender'].browse(self.env.context.get('active_id'))
        if not tender:
            raise UserError(_('No tender found.'))
        old_date = tender.date_submission
        tender.date_submission = self.new_date_submission
        tender.message_post(
            body=_('Submission deadline extended from %s to %s. Reason: %s') % (
                old_date, self.new_date_submission, self.reason
            ),
            subtype_xmlid="mail.mt_note"
        )
        return {'type': 'ir.actions.act_window_close'}
