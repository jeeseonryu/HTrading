from odoo import api, fields, models

class Stock_location_route(models.Model):
    _inherit = "stock.location.route"
    
    is_dropshipping = fields.Boolean("Is Dropshipping?")