from odoo import models,fields

class product_product(models.Model):
    _inherit = 'product.product'
    
    net_qty = fields.Float(compute='_calculate_total_qty')
    
    def _calculate_total_qty(self):
        for product in self:
            qty=0.0
            for seller in product.seller_ids:
                if seller.product_id and seller.product_id.id==product.id:
                    qty+= seller.vendor_product_qty
                if not seller.product_id:
                    qty+=seller.vendor_product_qty
            #added_qty = product.virtual_available if product.virtual_available >=0.0 else product.qty_available
            net_qty = qty + product.virtual_available
            product.net_qty=net_qty
                