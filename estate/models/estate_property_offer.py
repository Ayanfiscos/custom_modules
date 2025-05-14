from odoo import fields, models, api
from datetime import timedelta
from odoo import exceptions
from odoo.exceptions import UserError

class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Real Estate Property Offer"
    _order = "price desc"
   
    @api.model
    def create(self, vals):
        # Get the property record
        property_id = vals.get('property_id')
        property = self.env['estate.property'].browse(property_id)
        
        # Check if the new offer amount is greater than existing offers
        for offer in property.offer_ids:
            if vals.get('price') <= offer.price:
                raise exceptions.UserError("Cannot create an offer with lower price than existing offers!")
        
        # Create the record
        result = super().create(vals)
        
        # Update property state
        property.state = 'offer_received'
        
        return result

    price = fields.Float()
    status = fields.Selection([
        ('accepted', 'Accepted'),
        ('refused', 'Refused'),
    ], copy=False)
    partner_id = fields.Many2one("res.partner", string="Partner", required=True)
    property_id = fields.Many2one("estate.property", string="Property", required=True)
    property_type_id = fields.Many2one(related="property_id.property_type_id", store=True, string="Property Type")

    validity = fields.Integer(default=7)
    date_deadline = fields.Date(compute="_compute_date_deadline", inverse="_inverse_date_deadline", store=True)

    def action_accept_offer(self):
        for offer in self:
            if offer.property_id.state == "sold":
                raise UserError("Cannot accept offer on a sold property.")
            # Reject all other offers for the same property
            other_offers = self.search([
                ('property_id', '=', offer.property_id.id),
                ('id', '!=', offer.id)
            ])
            other_offers.write({'status': 'refused'})
            # Accept this one
            offer.status = 'accepted'
            offer.property_id.write({
                'buyer_id': offer.partner_id.id,
                'selling_price': offer.price,
                'state': 'offer_accepted'
            })
        return True

    def action_refuse_offer(self):
        for offer in self:
            offer.status = 'refused'
        return True

    @api.depends("create_date", "validity")
    def _compute_date_deadline(self):
        for record in self:
            # Ensure create_date is a datetime.date object, no need to call .date() again
            create_date = record.create_date or fields.Date.today()
            record.date_deadline = create_date + timedelta(days=record.validity)


    def _inverse_date_deadline(self):
        for record in self:
            # convert create_date to date
            create_date = (record.create_date or fields.Date.today()).date()
            if record.date_deadline:
                record.validity = (record.date_deadline - create_date).days
            else:
                record.validity = 0
                