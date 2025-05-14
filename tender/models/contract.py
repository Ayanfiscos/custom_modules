from odoo import models, fields, api

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
        ('closed', 'Closed'),
    ], string='Status', default='draft', tracking=True)
