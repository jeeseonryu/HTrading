from odoo import models,fields,api

class EdiConfiguration(models.Model):
    
    _name = "edi.configuration.ept"
    
    name = fields.Char(default="EDI Configuration")
    order_warehouse_id = fields.Many2one('stock.warehouse',string="Default Order Warehouse",required=True)
    stock_warehouse_ids = fields.Many2many('stock.warehouse',string="Default Stock Warehouses",required=True)
    order_number_from = fields.Selection([
                                        ('default', 'Default Sequence of Sale Order'),
                                        ('file', 'Order Number from File'),
                                        ('prefix_file', 'Prefix + Order Number from File'),
                                        ],default='default',required=True)
    auto_workflow_id = fields.Many2one('sale.workflow.process.ept',string="Default Workflow",required=True)