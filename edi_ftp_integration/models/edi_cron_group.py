from odoo import models,fields,api,_
from odoo.exceptions import except_orm, Warning, RedirectWarning 

class EDICronGroup(models.Model):
    
    _name = "edi.cron.group.ept"
    _description = "EDI Automation Group"
    
    name = fields.Char(string="Name",required=True)
    
    partner_ids = fields.Many2many('res.partner',compute="_get_partners",string="Partners")
    
    operation_type = fields.Selection([
                                        ('sale_import', 'Sale Order Import'),
                                        ('stock_export', 'Stock Export'),
                                        ('shipment_export', 'Tracking Export'),
                                        ('product_export', 'Product Export'),
                                        ],default='sale_import',required=True)
    
    cron_ids = fields.One2many('ir.cron','edi_group_id',string="Scheduled Actions",domain=['|',('active','=',False),('active','=',True)])
    active = fields.Boolean("Active",default=True)
    
    @api.multi
    def toggle_active(self):
        for group in self:
            group.write({'active': not group.active})
            if not group.active:
                group.cron_ids and group.cron_ids.write({'active':False})
            
    
    @api.multi
    def unlink(self):
        raise Warning(_("You are not allowed to delete automation group. Please Archive instead."))
    
    @api.multi
    def _get_partners(self):
        
        for record in self:
            
            partner_ids = self.env['res.partner'].search([('integrate_edi','=',True)])
            
            if not partner_ids:
                continue
            
            if record.operation_type == 'sale_import':
                filtered_ids = partner_ids.filtered(lambda x : x.sale_import_cron_group_id.id == record.id)
                record.partner_ids = [(6,0,filtered_ids.ids)] 
                
            if record.operation_type == 'stock_export':
                filtered_ids = partner_ids.filtered(lambda x : x.stock_export_cron_group_id.id == record.id)
                record.partner_ids = [(6,0,filtered_ids.ids)] 
                
            if record.operation_type == 'shipment_export':
                filtered_ids = partner_ids.filtered(lambda x : x.shipment_export_cron_group_id.id == record.id)
                record.partner_ids = [(6,0,filtered_ids.ids)] 
                
            if record.operation_type == 'product_export':
                filtered_ids = partner_ids.filtered(lambda x : x.product_export_cron_group_id.id == record.id)
                record.partner_ids = [(6,0,filtered_ids.ids)] 
        
        return True
        
    @api.model
    def perform_cron_execution(self,group_ids=[]):
        
        for group in group_ids:
            group = self.browse(group)
            if group.operation_type == 'sale_import':
                self.env['sale.order'].import_sale_orders_from_ftp(group.partner_ids,is_cron=True)
                
            if group.operation_type == 'stock_export':
                self.env['product.product'].export_inventory_to_partner_ftp(group.partner_ids,is_cron=True)
                
            if group.operation_type == 'shipment_export':
                self.env['stock.picking']._export_tracking_details_to_partner_ftp(group.partner_ids,is_cron=True)
                
            if group.operation_type == 'product_export':
                self.env['product.product'].export_products_to_partner_ftp(group.partner_ids,is_cron=True)
        
        return True
        