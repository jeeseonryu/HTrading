from odoo import api, fields, models, _

class PartnerProduct(models.Model):
    
    _name = 'partner.product.ept'
    _rec_name = 'product_id'
    
    partner_id = fields.Many2one('res.partner',string="Partner",required=True)
    product_id = fields.Many2one('product.product',string="Product",required=True)
    sku = fields.Char("Sku",required=True)
    
    _sql_constraints = [
        ('partner_product_unique', 'unique(partner_id,product_id,sku)', 'Combination of partner, product and sku must be unique'),
    ]