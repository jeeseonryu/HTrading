from odoo import models,fields,api
from .api import TPWFTPInterface

class ResPartner(models.Model):
    
    _inherit = "res.partner"
    
    integrate_edi = fields.Boolean(string="Allow EDI Integration?",default=False)
    ftp_server_id = fields.Many2one('ftp.server.ept',string="FTP Server")
    csv_delimiter = fields.Char(string="CSV Delimiter",default=";")
    auto_workflow_id= fields.Many2one('sale.workflow.process.ept',string="Auto Workflow")
    allow_shipment_export = fields.Boolean("Allow Tracking Export ?",default=False)
    allow_stock_export = fields.Boolean("Allow Stock Export ?",default=False)
    allow_product_export = fields.Boolean("Allow Product Export ?",default=False)
    
    prefix_product_export = fields.Char(string="Prefix Product Export")
    product_export_directory_id = fields.Many2one('ftp.directory.ept',string="Product Export Path",domain="[('ftp_server_id','=',ftp_server_id)]")
    
    prefix_sale_import = fields.Char(string="Sale Import Prefix")
    sale_import_directory_id = fields.Many2one('ftp.directory.ept',string="Sale Import Directory",domain="[('ftp_server_id','=',ftp_server_id)]")
    sale_archive_directory_id = fields.Many2one('ftp.directory.ept',string="Sale Archive Directory",domain="[('ftp_server_id','=',ftp_server_id)]")
    sale_warehouse_id = fields.Many2one('stock.warehouse',string="Sale Warehouse")
    order_number_from = fields.Selection([
                                    ('default', 'Default Configuration'),
                                    ('file', 'Order Number from File'),
                                    ('prefix_file', 'Prefix + Order Number from File'),
                                    ],default='default')
    order_number_prefix = fields.Char("Order Prefix")
    
    prefix_stock_export = fields.Char(string="Stock Export Prefix")
    stock_export_directory_id = fields.Many2one('ftp.directory.ept',string="Stock Export Path",domain="[('ftp_server_id','=',ftp_server_id)]")
    stock_warehouse_ids = fields.Many2many('stock.warehouse',string="Stock Warehouses")
    
    prefix_shipment_export = fields.Char(string="Shipment Export Prefix")
    shipment_export_directory_id = fields.Many2one('ftp.directory.ept',string="Shipment Export Path",domain="[('ftp_server_id','=',ftp_server_id)]")
    
    
    sale_import_cron_group_id = fields.Many2one('edi.cron.group.ept',string="Auto Sale Import Group",domain="[('operation_type','=','sale_import')]")
    product_export_cron_group_id = fields.Many2one('edi.cron.group.ept',string="Auto Product Export Group",domain="[('operation_type','=','product_export')]")
    shipment_export_cron_group_id = fields.Many2one('edi.cron.group.ept',string="Auto Shipment Export Group",domain="[('operation_type','=','shipment_export')]")
    stock_export_cron_group_id = fields.Many2one('edi.cron.group.ept',string="Auto Stock Export Group",domain="[('operation_type','=','stock_export')]")
    
    edi_log_ids = fields.One2many('edi.file.process.job','ftp_partner_id',string="File Logs")
    partner_product_ids = fields.One2many('partner.product.ept','partner_id',string="Partner Products")
    
    _sql_constraints = [
        ('order_prefix_unique', 'unique(order_number_prefix)', 'Order Prefix must be unique'),
    ]
    
    
        
    
    @api.multi
    def create_or_update_partner(self,vals,address_type=None):                        
        state_code = vals.get('state_code','')
        state_name = vals.get('state_name','')
        country_code = vals.get('country_code','')
        country_name = vals.get('country_name','')
        country_obj=self.env['res.country'].search(['|',('code','=',country_code),('name','=',country_name)],limit=1)
        state_obj = self.env['res.country.state'].search(['|',('name','=',state_name),('code','=',state_code),('country_id','=',country_obj.id)],limit=1)
        email = vals.get('email_id')
        name = vals.get('name')
        street = vals.get('street','')
        street2 = vals.get('street2','')
        phone = vals.get('phone','')
        city = vals.get('city','')
        zip = vals.get('postal-code','')
        
        domain = []
        domain.append(('name','=',name))
        domain.append(('street','=',street))
        domain.append(('street2','=',street2))
        domain.append(('city','=',city))
        domain.append(('state_id','=',state_obj.id))
        domain.append(('country_id','=',country_obj.id))
        domain.append(('zip','=',zip))
        domain.append(('email','=',email))
        domain.append(('phone','=',phone))
        
        partner_obj = self.env['res.partner'].search(domain,limit=1)
        if partner_obj:
            return partner_obj
        else:
            partnervals = {
                'name':name,
                'parent_id':vals.get('parent_id',''),
                'street':street,
                'street2':street2,
                'city':city,
                'state_id':state_obj.id or False,
                'country_id':country_obj.id or False,
                'phone':phone,
                'email':email,
                'zip':zip,
                'lang':vals.get('lang',''),
                'company_id':vals.get('company_id',''),
                'type':address_type,
                }
            partner = self.env['res.partner'].create(partnervals)
            return partner
        
    @api.model
    def get_edi_interface(self,operation):
        """
        Returns the credentials in tuple
        :param cursor: DB Cursor
        :param user: Integer ID of current user
        :param context: Context dictionary, no direct usage

        :return: An instantiated class of the tpwFTPInterface
        """
        
        host=self.ftp_server_id.ftp_host
        user_name=self.ftp_server_id.ftp_username
        password=self.ftp_server_id.ftp_password
        port=int(self.ftp_server_id.ftp_port)
        
        if operation=='product_export':
            edi_object=TPWFTPInterface(host,user_name,password,
                False,
                self.product_export_directory_id.path,
                False,
                port
            )    
            edi_object.set_pasv(self.ftp_server_id.is_passive_mode)
            return edi_object
        elif operation=='stock_export':
            edi_object=TPWFTPInterface(host,user_name,password,
                False,
                self.stock_export_directory_id.path,
                False,
                port
            )    
            edi_object.set_pasv(self.ftp_server_id.is_passive_mode)
            return edi_object
        elif operation=='sale_import':
            edi_object=TPWFTPInterface(host,user_name,password,
                self.sale_import_directory_id.path,
                False,
                self.sale_archive_directory_id.path,
                port
            )    
            edi_object.set_pasv(self.ftp_server_id.is_passive_mode)
            return edi_object
        elif operation=='shipment_export':
            edi_object=TPWFTPInterface(host,user_name,password,
                False,
                self.shipment_export_directory_id.path,
                False,
                port
            )    
            edi_object.set_pasv(self.ftp_server_id.is_passive_mode)
            return edi_object
  