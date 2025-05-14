from odoo import models
from odoo.models import Command

class EstateProperty(models.Model):
    _inherit = "estate.property"

    def action_set_sold(self):  # Make sure this matches your base method name
        # Debug print
        print("Property sold! Now we can create an invoice.")
        
        # Create invoice
        invoice_vals = {
            'partner_id': self.buyer_id.id,
            'move_type': 'out_invoice',  # Customer invoice
            # You might need to find an appropriate journal
            'journal_id': self.env['account.journal'].search([('type', '=', 'sale')], limit=1).id,
            'invoice_line_ids': [
                # Line 1: 6% of selling price
                Command.create({
                    'name': f'6% of the selling price for {self.name}',
                    'quantity': 1.0,
                    'price_unit': self.selling_price * 0.06,
                }),
                # Line 2: Administrative fee
                Command.create({
                    'name': 'Administrative fees',
                    'quantity': 1.0,
                    'price_unit': 100.00,
                }),
            ],
        }
        
        # Create the invoice
        self.env['account.move'].create(invoice_vals)
        
        # Call the original method
        return super().action_set_sold()