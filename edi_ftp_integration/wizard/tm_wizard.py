from openerp import models,fields,api

class EdiOperationWizard(models.TransientModel):
    
    _name="edi.operations.wizard"
    
    partner_ids = fields.Many2many('res.partner',string="Customers",required=True)
    export_products = fields.Boolean('Export Products')
    import_orders = fields.Boolean('Import Orders')
    export_shipments = fields.Boolean('Export Shipments')
    export_inventory = fields.Boolean('Export Inventory')
    
    @api.multi
    def perform_operations(self):
                
        product_obj=self.env['product.product']
        stock_picking=self.env['stock.picking']
        sale_order_obj = self.env['sale.order']
        
        if self.export_products:
            product_obj.with_context({'run_manually' : True}).export_products_to_partner_ftp(self.partner_ids)
        if self.import_orders:  
            sale_order_obj.with_context({'run_manually' : True}).import_sale_orders_from_ftp(self.partner_ids)  
        if self.export_shipments:
            stock_picking.with_context({'run_manually' : True})._export_tracking_details_to_partner_ftp(self.partner_ids)
        if self.export_inventory:
            product_obj.with_context({'run_manually' : True}).export_inventory_to_partner_ftp(self.partner_ids)

        return True
