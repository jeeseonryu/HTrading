from odoo import models,fields,api,_

class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"
    
    vendor_product_qty = fields.Float('Product Quantity')
        
        