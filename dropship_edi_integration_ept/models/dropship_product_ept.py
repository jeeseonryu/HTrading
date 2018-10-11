from odoo import models, fields, api
from .api import TPWFTPInterface

class DropshipProducts(models.Model):
    _name = "dropship.product.ept"
    _description = "Dropship Products"
    _inherit = ['mail.thread']
    _order='id desc'
    
    name = fields.Char(string='Product')
    main_product_id = fields.Char(string="Main Product ID")
    partner_id = fields.Many2one('res.partner', 'Partner')
    is_processed = fields.Boolean(string="Is Processed?", default=False)
    dropship_product_line = fields.One2many('dropship.product.line.ept', 'dropship_order_id', string='Product Lines')
    filename = fields.Char("File Name")

class DropshipProductLine(models.Model):
    _name = "dropship.product.line.ept"
    _description = 'Dropship Product Line'
    _order = 'dropship_order_id'
    
    dropship_order_id = fields.Many2one('dropship.product.ept',ondelete='cascade', string='Product')
    name = fields.Char(string="Name")
    default_code = fields.Char(string="Default Code")
    vendor_code = fields.Char(string="Vendor Code")
    description = fields.Text(string="Description")
    attribute_name = fields.Char(string="Attributes")
    attribute_value = fields.Char(string="Attribute Values")
    price = fields.Float(string="Price")
    category = fields.Char(string="Category")
    product_id = fields.Many2one('product.product', 'Product')
    barcode = fields.Char(string="Barcode")
    image_url = fields.Text(string="Image URL")
    weight = fields.Float(string="Weight")
    tags = fields.Char(string = "Tags")
    
    
    