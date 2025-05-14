from odoo import fields, models

class ResUsers(models.Model):
    _inherit = "res.users"

    property_ids = fields.One2many(
        "estate.property", 
        "salesperson_id",  # Assuming this field exists in estate.property
        string="Properties",
        domain=[('state', '=', 'available')]  # Only show available properties
    )