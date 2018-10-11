from odoo import models,fields,api,_

class product_creation_process_ept(models.TransientModel):
    _name = "product.creation.process.ept"
    
    dropship_product_ids = fields.Many2many('dropship.product.ept',string="Products")
    partner_id = fields.Many2one('res.partner',string="Supplier")