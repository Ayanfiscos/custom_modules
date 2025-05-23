from odoo import models, fields, api
from odoo.exceptions import UserError

class Contract(models.Model):
    _name = "tender.contract"
    _description = "Contract"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Contract Title', required=True, tracking=True)
    company_name = fields.Char(string='Company Name', required=True, tracking=True)
    tender_id = fields.Many2one('tender.tender', string='Related Tender', required=True, ondelete='cascade')
    contract_reference = fields.Char(string='Contract Reference Number', required=True, tracking=True)
    start_date = fields.Date(string='Start Date', required=True, tracking=True)
    end_date = fields.Date(string='End Date', required=True, tracking=True)
    approved_amount = fields.Float(string='Approved Amount', tracking=True)
    tender_outcome = fields.Selection([
        ('won', 'won'),
    ], required=True, readonly=True)
    state = fields.Selection([
        ('draft', 'Draft Contract'),
        ('negotiation', 'Under Negotiation'),
        ('final', 'Final Contract'),
        ('executed', 'Executed'),
    ], string='Status', default='draft', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', tracking=True, default=lambda self: self.env.company)
    duration_of_contract = fields.Char(
        string="Duration of Contract",
        compute='_compute_duration_of_contract',
        store=True  # This ensures the value is stored in database
    )
    extension_option = fields.Char(string="Extension Option")
    reviewed_date = fields.Date(string="Reviewed Date")
    comment = fields.Text(string="Comment")

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super().fields_view_get(view_id, view_type, toolbar, submenu)
        return res

    @api.model
    def _register_hook(self):
        # Ensure all workflow methods are registered
        return super()._register_hook()

    # Workflow actions for contract state transitions
    def action_negotiate(self):
        for rec in self:
            if rec.state == 'draft':
                rec.state = 'negotiation'

    def action_open_tender(self):
        if not self.tender_id:
            raise UserError("There is no Tender for this Contract.")
        # Return the action to open the existing tender
        return {
            'type': 'ir.actions.act_window',
            'name': 'Open Tender',
            'res_model': 'tender.tender',
            'view_mode': 'form',
            'res_id': self.tender_id.id,  # Open the specific tender (use .id)
            'target': 'current',
        }
    
    def action_finalize(self):
        for rec in self:
            if rec.state == 'negotiation':
                rec.state = 'final'

    def action_execute(self):
        for rec in self:
            if rec.state == 'final':
                rec.state = 'executed'

    def action_reset(self):
        for rec in self:
            rec.state = 'draft'

    @api.depends('start_date', 'end_date')
    def _compute_duration_of_contract(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                start = fields.Date.from_string(str(rec.start_date))
                end = fields.Date.from_string(str(rec.end_date))
                months = (end.year - start.year) * 12 + (end.month - start.month)
                if end.day < start.day:
                    months -= 1
                rec.duration_of_contract = f"{months} months" if months >= 0 else "0 months"
            else:
                rec.duration_of_contract = False
