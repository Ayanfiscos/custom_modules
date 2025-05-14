from odoo import fields, models

class EstatePropertyTag(models.Model):
    _name = "estate.property.tag"
    _description = "Real Estate Property Tag"
    _order = "sequence, name"

    name = fields.Char(required=True)
    color = fields.Integer(string="Color")
    sequence = fields.Integer(string="Sequence", default=10)