from odoo import models,fields,api,_
from io import StringIO
from datetime import datetime
import base64
from .api import UnicodeDictWriter,UnicodeDictReader
import time
from odoo.exceptions import except_orm, Warning, RedirectWarning 
from odoo.api import Environment
from dateutil import parser
import os
from csv import DictWriter
import logging
_logger = logging.getLogger(__name__)

class ProdutProduct(models.Model):
    
    _inherit = 'product.product'
    
    web_categories = fields.Many2many('product.category',string="Website Categories")
    youtube_url = fields.Char(string="Youtube Url")
    description_website = fields.Html('Website Description')
    description_quote = fields.Text("Quotation Description")
    
    @api.model
    def find_value_lenth_with_maximum_attribute_value(self,product_ids=[]):
        
            
        attribute_products = product_ids.filtered(lambda x: len(x.product_id.attribute_value_ids) >0 )
        lenth_of_value_ids = 0
        for product in attribute_products:
            if len(product.product_id.attribute_value_ids) > lenth_of_value_ids:
                lenth_of_value_ids = len(product.product_id.attribute_value_ids)
        return lenth_of_value_ids
    
    @api.multi
    def get_product_from_sku(self,partner,product_code):
        partner_product = self.env['partner.product.ept'].search([('partner_id','=',partner.id),('sku','=',product_code)],limit=1)
        product = None
        if not partner_product:
            product = self.search([('default_code','=',product_code)],limit=1)
        else:
            product = partner_product.product_id
        return product
            
    @api.multi        
    def export_products_to_partner_ftp(self,partner_ids=[],is_cron=False):
        if not partner_ids:
            partner_ids = self.env['res.partner'].search([('integrate_edi','=',True),('allow_product_export','=',True)])
            
        transaction_log_obj=self.env['edi.transaction.log']
        
        for partner in partner_ids:
            
            if not partner.allow_product_export:
                continue
            
            if not partner.integrate_edi:
                continue
            
            export_time = datetime.now()
            filename = "%s_%s" %(partner.prefix_product_export or "Export_Stock",export_time.strftime('%Y%m%d%H%M%S.csv'))
            job=self.env['edi.file.process.job'].create({'application':'product'
                                             ,'operation_type':'export',
                                             'ftp_partner_id':partner.id,
                                             'filename':filename})

            buffer = StringIO()
            field_names = ['Main_product_id','Price','Category','Tags','Description','Attributes','Attribute_values','Product_code','Image_url','Barcode','Weight','Title']

            if partner.partner_product_ids:
                            
                csvwriter = DictWriter(buffer, field_names, delimiter=partner.csv_delimiter or ';')
                csvwriter.writer.writerow(field_names)
                
                # Get Price
                pricelist = partner.property_product_pricelist
                
                for partner_product in partner.partner_product_ids:
                    sku = partner_product.sku
                    erp_product = partner_product.product_id
                    price = erp_product.lst_price
                    if pricelist:
                        price = pricelist.price_get(erp_product.id,1)[pricelist.id] or 0.0
                    
                    write_row = {
                        'Main_product_id':erp_product.default_code or '',
                        'Product_code':erp_product.default_code or '',
                        'Price':price or 0.0,
                        'Category':erp_product.categ_id and erp_product.categ_id.display_name or '',
                        'Tags':'',
                        'Description':erp_product.description_sale or '',
                        'Attributes':'',
                        'Attribute_values':'',
                        'Image_url':'',
                        'Barcode':erp_product.barcode or '',
                        'Weight':erp_product.weight or 0.0,
                        'Title':erp_product.name,  
                    }
                    
                    attributes = []
                    values = []
                    for attribute_value in erp_product.attribute_value_ids:
                        attributes.append(attribute_value.attribute_id.name)
                        values.append(attribute_value.name)
                    
                    if erp_product.attribute_value_ids: 
                        comma_separate = ","
                        attributes = comma_separate.join(attributes)
                        values = comma_separate.join(values)
                        write_row.update({'Attributes':attributes or '','Attribute_values':values or ''})
                        
                    write_row.update({'Description':erp_product.description_sale or ''})
                    csvwriter.writerow(write_row)
                    
                    transaction_log_obj.create({
                            'product_id': erp_product.id,
                            'job_id': job.id,
                            'is_processed': True,
                            'message': "Product Exported"
                        })
                    
                # Export Data to Partner's FTP Server
                export_time = datetime.now()
                filename = "%s_%s" %(partner.prefix_product_export or "Export_Product",export_time.strftime('%Y%m%d%H%M%S.csv'))
                
                try:
                    with partner.get_edi_interface(operation="product_export") as edi_interface:
                        buffer.seek(0)
                        edi_interface.push_to_ftp(filename, buffer) 
                except:
                    if is_cron:
                        job.write({'message': "Problem with connection or file Path. File not exported to Partner's FTP."})
                    else:
                        raise Warning(_("Problem with FTP connection. Please check credentials and file paths"))
                    
                buffer.seek(0)
                file_data = buffer.read().encode()
                vals = {
                        'name':filename,
                        'datas':base64.encodestring(file_data),
                        'datas_fname':filename,
                        'type':'binary',
                        'res_model': 'edi.file.process.job',
                        }
                attachment=self.env['ir.attachment'].create(vals)
                job.message_post(body=_("<b>Products Exported File</b>"),attachment_ids=attachment.ids)
                buffer.close()
            
        return True
    
    @api.model
    def export_inventory_to_partner_ftp(self,partner_ids=[],is_cron=False):
        
        if not partner_ids:
            partner_ids = self.env['res.partner'].search([('integrate_edi','=',True)])
            
        transaction_log_obj=self.env['edi.transaction.log']
        for partner in partner_ids:
            
            if not partner.allow_stock_export:
                continue
            
            export_time = datetime.now()
            filename = "%s_%s" %(partner.prefix_stock_export or "Export_Stock",export_time.strftime('%Y%m%d%H%M%S.csv'))
            job=self.env['edi.file.process.job'].create({'application':'invenotry'
                                             ,'operation_type':'export',
                                             'ftp_partner_id':partner.id,
                                             'filename':filename})
            
            if not partner.integrate_edi:
                continue
            
            if not partner.partner_product_ids:
                continue
            
            buffer = StringIO()
            field_names = [
                'sku',
                'quantity',
            ]
            csvwriter = DictWriter(buffer, field_names, delimiter=partner.csv_delimiter or ';')
            csvwriter.writer.writerow(field_names)
            
            # Prepare CSV
            # Unique Data with Partner's SKU
            for partner_product in partner.partner_product_ids:
                sku = partner_product.sku
                erp_product = partner_product.product_id
                
                warehouses = partner.stock_warehouse_ids
                
                if not warehouses:
                    default_setting = self.env.ref('edi_ftp_integration.edi_default_configuration')
                    warehouses = default_setting.stock_warehouse_ids
                    
                quantity = erp_product.with_context(warehouse=warehouses.ids).qty_available
                csvwriter.writerow({'sku':sku,
                                    'quantity':quantity})

                transaction_log_obj.create({
                        'product_id': partner_product.product_id.id,
                        'file_quantity': quantity,
                        'file_sku':sku,
                        'job_id': job.id,
                        'is_processed': True,
                        'message': "Stock Exported"
                    })
                
            # Export Data to Partner's FTP Server
            export_time = datetime.now()
            filename = "%s_%s" %(partner.prefix_stock_export or "Export_Stock",export_time.strftime('%Y%m%d%H%M%S.csv'))
            
            try:
                with partner.get_edi_interface(operation="stock_export") as edi_interface:
                    buffer.seek(0)
                    edi_interface.push_to_ftp(filename, buffer) 
            except:
                if is_cron:
                    job.write({'message': "Problem with connection or file Path. File not exported to Partner's FTP."})
                else:
                    raise Warning(_("Problem with FTP connection. Please check credentials and file paths"))
                
            buffer.seek(0)
            file_data = buffer.read().encode()
            vals = {
                    'name':filename,
                    'datas':base64.encodestring(file_data),
                    'datas_fname':filename,
                    'type':'binary',
                    'res_model': 'edi.file.process.job',
                    }
            attachment=self.env['ir.attachment'].create(vals)
            job.message_post(body=_("<b>Stock Exported File</b>"),attachment_ids=attachment.ids)
            buffer.close()
            
        return True
                