from odoo import models, fields, api
from .api import TPWFTPInterface
from datetime import datetime
from dateutil.relativedelta import relativedelta

_intervalTypes = {
    'work_days': lambda interval: relativedelta(days=interval),
    'days': lambda interval: relativedelta(days=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'weeks': lambda interval: relativedelta(days=7*interval),
    'months': lambda interval: relativedelta(months=interval),
    'minutes': lambda interval: relativedelta(minutes=interval),
}

class ResPartner(models.Model):
    _inherit = "res.partner"
    
    is_integrate_edi = fields.Boolean(string="Allow DropShip EDI Integration?", default=False)
    dropship_server_id = fields.Many2one('drop.ship.server.ept', string="FTP Server")
    csv_delimiter = fields.Char(string="CSV Delimiter", default=";")

#     allow_import_product = fields.Boolean(string="Import Product?", default=False)
    prefix_allow_import_product = fields.Char(string="Prefix Import Product")
    product_import_directory_id = fields.Many2one('directory.ept', string="Product Import Path", domain="[('server_id','=',dropship_server_id)]")
    search_by_vendor_code = fields.Boolean(string="Search By Vendor Code?",help="If True it will set product code into Vendor Code Otherwise it will set in Product Code while you Import the Products From FTP")
    product_archive_directory_id = fields.Many2one('directory.ept', string="Product Archive Path", domain="[('server_id','=',dropship_server_id)]")
    auto_create_category = fields.Boolean(string="Auto Create Product Category if not found?", default=False)
    
    #Auto import Product Schedular action
    auto_import_product = fields.Boolean(string="Auto Import Product From FTP?", default=False)
    product_import_interval_number = fields.Integer('Product Import Interval Number',help="Repeat every x.")
    product_import_interval_type = fields.Selection( [('minutes', 'Minutes'),
            ('hours','Hours'), ('work_days','Work Days'), ('days', 'Days'),('weeks', 'Weeks'), ('months', 'Months')], 'Product Import Interval Unit')
    product_import_next_execution = fields.Datetime('Next Execution', help='Next execution time')
    product_import_user_id = fields.Many2one('res.users',string="User",help='User',default=lambda self: self.env.user)
    
    #For Schedular action
    auto_create_product = fields.Boolean(string="Auto Create/Update Product ?", default=False)
    product_creation_interval_number = fields.Integer('Product Import Interval Number',help="Repeat every x.")
    product_creation_interval_type = fields.Selection( [('minutes', 'Minutes'),
            ('hours','Hours'), ('work_days','Work Days'), ('days', 'Days'),('weeks', 'Weeks'), ('months', 'Months')], 'Product Creation Interval Unit')
    product_creation_next_execution = fields.Datetime('Next Execution', help='Next execution time')
    product_creation_user_id = fields.Many2one('res.users',string="User",help='User',default=lambda self: self.env.user)
    
    stock_import_interval_number = fields.Integer('Stock Import Interval Number',help="Repeat every x.")
    stock_import_interval_type = fields.Selection( [('minutes', 'Minutes'),
            ('hours','Hours'), ('work_days','Work Days'), ('days', 'Days'),('weeks', 'Weeks'), ('months', 'Months')], 'Product Import Interval Unit')
    stock_import_next_execution = fields.Datetime('Next Execution', help='Next execution time')
    stock_import_user_id = fields.Many2one('res.users',string="User",help='User',default=lambda self: self.env.user)
    prefix_import_stock = fields.Char(string="Prefix Import Stock")
    stock_import_directory_id = fields.Many2one('directory.ept', string="Stock Import Path", domain="[('server_id','=',dropship_server_id)]")
    auto_validate_inventory = fields.Boolean(string="Auto import Inventory Stock?", default=False)
    stock_archive_directory_id = fields.Many2one('directory.ept', string="Stock Archive Path", domain="[('server_id','=',dropship_server_id)]")
    
    
    order_import_interval_number = fields.Integer('Import Shipment Interval Number',help="Repeat every x.")
    order_import_interval_type = fields.Selection( [('minutes', 'Minutes'),
            ('hours','Hours'), ('work_days','Work Days'), ('days', 'Days'),('weeks', 'Weeks'), ('months', 'Months')], 'Import Order Interval Unit')
    order_import_next_execution = fields.Datetime('Next Execution', help='Next execution time')
    order_import_user_id = fields.Many2one('res.users',string="User",help='User',default=lambda self: self.env.user)
    prefix_shipment_tracking = fields.Char(string="Prefix Shipment Information")
    shipment_import_directory_id = fields.Many2one('directory.ept', string="Shipment Import Path", domain="[('server_id','=',dropship_server_id)]")
    shipment_archive_directory_id = fields.Many2one('directory.ept', string="Shipment Archive Path", domain="[('server_id','=',dropship_server_id)]")
    is_auto_import_shipments = fields.Boolean(string="Auto Import shipment?", default=False)
    
    order_export_interval_number = fields.Integer('Export Orders Interval Number',help="Repeat every x.")
    order_export_interval_type = fields.Selection( [('minutes', 'Minutes'),
            ('hours','Hours'), ('work_days','Work Days'), ('days', 'Days'),('weeks', 'Weeks'), ('months', 'Months')], 'Export Order Interval Unit')
    order_export_next_execution = fields.Datetime('Next Execution', help='Next execution time')
    order_export_user_id = fields.Many2one('res.users',string="User",help='User',default=lambda self: self.env.user)
    prefix_allow_shipment_export = fields.Char(string="Prefix Export Shipment")
    drophip_shipment_export_directory_id = fields.Many2one('directory.ept', string="Shipment Export Path", domain="[('server_id','=',dropship_server_id)]")
    is_auto_export_orders = fields.Boolean(string="Auto Export Orders?", default=False)
    
    dropship_log_ids = fields.One2many('dropship.file.process.job.ept', 'partner_id', string="File Logs")     

    @api.model
    def get_dropship_edi_interface(self, operation):
        
        host = self.dropship_server_id.host
        user_name = self.dropship_server_id.username
        password = self.dropship_server_id.password
        port = int(self.dropship_server_id.port)
        
        if operation == 'product_import':
            dropship_edi_object = TPWFTPInterface(host, user_name, password,self.product_import_directory_id.path,False,self.product_archive_directory_id.path,port)
            return dropship_edi_object
        elif operation == 'stock_import':
            dropship_edi_object = TPWFTPInterface(host, user_name, password,self.stock_import_directory_id.path,False,self.stock_archive_directory_id.path,port)
            return dropship_edi_object
        elif operation == 'shipment_export':
            dropship_edi_object = TPWFTPInterface(host, user_name, password,False,self.drophip_shipment_export_directory_id.path,False, port)
            return dropship_edi_object
        elif operation == 'shipment_import':
            dropship_edi_object = TPWFTPInterface(host, user_name, password,self.shipment_import_directory_id.path,False,self.shipment_archive_directory_id.path,port)
            return dropship_edi_object

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        self.setup_auto_import_product_from_ftp_cron()
        self.setup_auto_create_product_from_temp_data_cron()
        self.setup_auto_export_dropship_orders_cron()
        self.setup_auto_import_validate_orders_cron()
        self.setup_auto_import_inventory_stock_cron()
        return res
    
    @api.multi
    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        self.setup_auto_import_product_from_ftp_cron()
        self.setup_auto_create_product_from_temp_data_cron()
        self.setup_auto_export_dropship_orders_cron()
        self.setup_auto_import_validate_orders_cron()
        self.setup_auto_import_inventory_stock_cron()
        return res
    
    @api.multi   
    def setup_auto_import_inventory_stock_cron(self):
        if self.auto_validate_inventory:
            try:  
                cron_exist = self.env.ref('dropship_edi_integration_ept.ir_cron_dropship_import_stock_from_ftp_supplier_%d'%(self.id),raise_if_not_found=False)
            except:
                cron_exist=False
            nextcall = datetime.now()
            nextcall += _intervalTypes[self.stock_import_interval_type](self.stock_import_interval_number)
            vals = {'active' : True,
                    'interval_number':self.stock_import_interval_number,
                    'interval_type':self.stock_import_interval_type,
                    'nextcall':nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                    'code':"model.auto_import_inventory_stock_from_ftp(ctx={'partner_id':%d})"%(self.id),
                    'user_id': self.stock_import_user_id and self.stock_import_user_id.id}
            if cron_exist:
                vals.update({'name' : cron_exist.name})
                cron_exist.write(vals)
            else:
                try:                    
                    import_stock_from_ftp_cron = self.env.ref('dropship_edi_integration_ept.ir_cron_dropship_import_stock_from_ftp')
                except:
                    import_stock_from_ftp_cron=False
                if not import_stock_from_ftp_cron:
                    raise Warning('Core settings of Auto Import Inventory Stock Information are deleted, please upgrade Dropshipping Connector module to back this settings.')
                
                name = self.name + ' : ' +import_stock_from_ftp_cron.name
                vals.update({'name':name})
                new_cron = import_stock_from_ftp_cron.copy(default=vals)
                self.env['ir.model.data'].create({'module':'dropship_edi_integration_ept',
                                                  'name':'ir_cron_dropship_import_stock_from_ftp_supplier_%d'%(self.id),
                                                  'model': 'ir.cron',
                                                  'res_id' : new_cron.id,
                                                  'noupdate' : True
                                                  })
        else:
            try:
                cron_exist = self.env.ref('dropship_edi_integration_ept.ir_cron_dropship_import_stock_from_ftp_supplier_%d'%(self.id))
            except:
                cron_exist=False
            if cron_exist:
                cron_exist.write({'active':False})        
        return True
    
    
    @api.multi   
    def setup_auto_import_validate_orders_cron(self):
        if self.is_auto_import_shipments:
            try:  
                cron_exist = self.env.ref('dropship_edi_integration_ept.ir_cron_dropship_import_shipments_from_ftp_supplier_%d'%(self.id),raise_if_not_found=False)
            except:
                cron_exist=False
            nextcall = datetime.now()
            nextcall += _intervalTypes[self.order_import_interval_type](self.order_import_interval_number)
            vals = {'active' : True,
                    'interval_number':self.order_import_interval_number,
                    'interval_type':self.order_import_interval_type,
                    'nextcall':nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                    'code':"model.auto_import_shipment_details_from_ftp(ctx={'partner_id':%d})"%(self.id),
                    'user_id': self.order_import_user_id and self.order_import_user_id.id}
            if cron_exist:
                vals.update({'name' : cron_exist.name})
                cron_exist.write(vals)
            else:
                try:                    
                    import_orders_from_ftp_cron = self.env.ref('dropship_edi_integration_ept.ir_cron_dropship_import_shipments_from_ftp')
                except:
                    import_orders_from_ftp_cron=False
                if not import_orders_from_ftp_cron:
                    raise Warning('Core settings of Auto Import Shipment Information are deleted, please upgrade Dropshipping Connector module to back this settings.')
                
                name = self.name + ' : ' +import_orders_from_ftp_cron.name
                vals.update({'name':name})
                new_cron = import_orders_from_ftp_cron.copy(default=vals)
                self.env['ir.model.data'].create({'module':'dropship_edi_integration_ept',
                                                  'name':'ir_cron_dropship_import_shipments_from_ftp_supplier_%d'%(self.id),
                                                  'model': 'ir.cron',
                                                  'res_id' : new_cron.id,
                                                  'noupdate' : True
                                                  })
        else:
            try:
                cron_exist = self.env.ref('dropship_edi_integration_ept.ir_cron_dropship_import_shipments_from_ftp_supplier_%d'%(self.id))
            except:
                cron_exist=False
            if cron_exist:
                cron_exist.write({'active':False})        
        return True
    
    @api.multi   
    def setup_auto_export_dropship_orders_cron(self):
        if self.is_auto_export_orders:
            try:  
                cron_exist = self.env.ref('dropship_edi_integration_ept.ir_cron_dropship_export_Orders_to_ftp_supplier_%d'%(self.id),raise_if_not_found=False)
            except:
                cron_exist=False
            nextcall = datetime.now()
            nextcall += _intervalTypes[self.order_export_interval_type](self.order_export_interval_number)
            vals = {'active' : True,
                    'interval_number':self.order_export_interval_number,
                    'interval_type':self.order_export_interval_type,
                    'nextcall':nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                    'code':"model.auto_export_orders_detail_to_ftp(ctx={'partner_id':%d})"%(self.id),
                    'user_id': self.order_export_user_id and self.order_export_user_id.id}
            if cron_exist:
                vals.update({'name' : cron_exist.name})
                cron_exist.write(vals)
            else:
                try:                    
                    export_orders_from_ftp_cron = self.env.ref('dropship_edi_integration_ept.ir_cron_dropship_export_Orders_to_ftp')
                except:
                    export_orders_from_ftp_cron=False
                if not export_orders_from_ftp_cron:
                    raise Warning('Core settings of Auto Export Dropship Orders are deleted, please upgrade Dropshipping Connector module to back this settings.')
                
                name = self.name + ' : ' +export_orders_from_ftp_cron.name
                vals.update({'name':name})
                new_cron = export_orders_from_ftp_cron.copy(default=vals)
                self.env['ir.model.data'].create({'module':'dropship_edi_integration_ept',
                                                  'name':'ir_cron_dropship_export_Orders_to_ftp_supplier_%d'%(self.id),
                                                  'model': 'ir.cron',
                                                  'res_id' : new_cron.id,
                                                  'noupdate' : True
                                                  })
        else:
            try:
                cron_exist = self.env.ref('dropship_edi_integration_ept.ir_cron_dropship_export_Orders_to_ftp_supplier_%d'%(self.id))
            except:
                cron_exist=False
            if cron_exist:
                cron_exist.write({'active':False})        
        return True
    
    @api.multi   
    def setup_auto_import_product_from_ftp_cron(self):
        if self.auto_import_product:
            try:  
                cron_exist = self.env.ref('dropship_edi_integration_ept.ir_cron_dropship_import_products_from_ftp_supplier_%d'%(self.id),raise_if_not_found=False)
            except:
                cron_exist=False
            nextcall = datetime.now()
            nextcall += _intervalTypes[self.product_import_interval_type](self.product_import_interval_number)
            vals = {'active' : True,
                    'interval_number':self.product_import_interval_number,
                    'interval_type':self.product_import_interval_type,
                    'nextcall':nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                    'code':"model.auto_import_products_from_ftp(ctx={'partner_id':%d})"%(self.id),
                    'user_id': self.product_import_user_id and self.product_import_user_id.id}
            if cron_exist:
                vals.update({'name' : cron_exist.name})
                cron_exist.write(vals)
            else:
                try:                    
                    import_product_from_ftp_cron = self.env.ref('dropship_edi_integration_ept.ir_cron_dropship_import_products_from_ftp')
                except:
                    import_product_from_ftp_cron=False
                if not import_product_from_ftp_cron:
                    raise Warning('Core settings of Auto Import Products are deleted, please upgrade Dropshipping Connector module to back this settings.')
                
                name = self.name + ' : ' +import_product_from_ftp_cron.name
                vals.update({'name':name})
                new_cron = import_product_from_ftp_cron.copy(default=vals)
                self.env['ir.model.data'].create({'module':'dropship_edi_integration_ept',
                                                  'name':'ir_cron_dropship_import_products_from_ftp_supplier_%d'%(self.id),
                                                  'model': 'ir.cron',
                                                  'res_id' : new_cron.id,
                                                  'noupdate' : True
                                                  })
        else:
            try:
                cron_exist = self.env.ref('dropship_edi_integration_ept.ir_cron_dropship_import_products_from_ftp_supplier_%d'%(self.id))
            except:
                cron_exist=False
            if cron_exist:
                cron_exist.write({'active':False})        
        return True
    
    @api.multi   
    def setup_auto_create_product_from_temp_data_cron(self):
        if self.auto_create_product:
            try:                
                cron_exist = self.env.ref('dropship_edi_integration_ept.ir_cron_dropship_create_or_update_products_supplier_%d'%(self.id),raise_if_not_found=False)
            except:
                cron_exist=False
            nextcall = datetime.now()
            nextcall += _intervalTypes[self.product_creation_interval_type](self.product_creation_interval_number)
            vals = {'active' : True,
                    'interval_number':self.product_creation_interval_number,
                    'interval_type':self.product_creation_interval_type,
                    'nextcall':nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                    'code':"model.auto_create_or_update_products(ctx={'partner_id':%d})"%(self.id),
                    'user_id': self.product_creation_user_id and self.product_creation_user_id.id}
            if cron_exist:
                vals.update({'name' : cron_exist.name})
                cron_exist.write(vals)
            else:
                try:                    
                    create_product_from_temp_cron = self.env.ref('dropship_edi_integration_ept.ir_cron_dropship_create_or_update_products')
                except:
                    create_product_from_temp_cron=False
                if not create_product_from_temp_cron:
                    raise Warning('Core settings of Create or Update Products From Intermediate are deleted, please upgrade Dropshipping Connector module to back this settings.')
                name = self.name + ' : ' +create_product_from_temp_cron.name
                vals.update({'name':name})
                new_cron = create_product_from_temp_cron.copy(default=vals)
                self.env['ir.model.data'].create({'module':'dropship_edi_integration_ept',
                                                  'name':'ir_cron_dropship_create_or_update_products_supplier_%d'%(self.id),
                                                  'model': 'ir.cron',
                                                  'res_id' : new_cron.id,
                                                  'noupdate' : True
                                                  })
        else:
            try:
                cron_exist = self.env.ref('dropship_edi_integration_ept.ir_cron_dropship_create_or_update_products_supplier_%d'%(self.id))
            except:
                cron_exist=False
            if cron_exist:
                cron_exist.write({'active':False})        
        return True
    
          