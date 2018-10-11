from odoo import models,fields,api

class DropshipOperationWizard(models.TransientModel):
    _name="dropship.operations"
    
    partner_ids = fields.Many2many('res.partner',string="Suppliers")
    product_ids = fields.Many2many('dropship.product.ept',string="Products")
    picking_ids = fields.Many2many('stock.picking', string="Purchase Orders")
    import_products = fields.Boolean('Import Products Data')
    create_product_data = fields.Boolean('Create Product Data')
    import_inventory = fields.Boolean('Import Stock')
    import_shipment_info = fields.Boolean('Get Shipment Informations')
    export_shipment_orders = fields.Boolean('Export Orders')
    
    @api.multi
    def perform_operations(self): 
        
        product_obj=self.env['product.product']
        product_template = self.env['product.template']
        stock_picking_obj = self.env['stock.picking']
        
        if self.import_products:
            product_obj.import_products_from_ftp(self.partner_ids)
        elif self.import_inventory:
            product_obj.import_inventory_stock_from_ftp(self.partner_ids)
        elif self.create_product_data:
            product_template.create_or_update_products(self.product_ids,self.partner_ids,is_cron=False)
        elif self.export_shipment_orders:
            stock_picking_obj.export_orders_detail_to_ftp(self.picking_ids,self.partner_ids)
        elif self.import_shipment_info:
            stock_picking_obj.import_shipment_details_from_ftp(self.partner_ids)
        return True
    
