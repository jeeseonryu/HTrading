from odoo import api, fields, models, _

class PickingType(models.Model):
    _inherit = "stock.picking.type"
    
    is_dropship_process = fields.Boolean(string="Is Dropshiping?",defaul=False)