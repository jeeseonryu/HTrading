from odoo import models,fields,api,_
from datetime import datetime
from odoo.exceptions import except_orm, Warning, RedirectWarning 
from odoo.api import Environment
import csv
import base64
import logging
_logger = logging.getLogger(__name__)

class product_product(models.Model):
    _inherit = 'product.product'
    
    tags = fields.Char(string='Tags')
    
    @api.multi
    def validate_data(self, sale_data=[],job=False,partner_id=False,server_filename=False,filename=False):
        row_num = 1
        updated_product = 0
        created_product = 0
        transaction_log_obj=self.env['dropship.transaction.log.ept']
        for line in sale_data:
            dropship_product_ept_obj = self.env['dropship.product.ept']
            dropship_product_line_ept_obj = self.env['dropship.product.line.ept']
            
            missing_values = []
            main_product_id = line.get('Main_product_id',False)
            description = line.get('Description',False)
            tags = line.get('Tags',False)
            attributes = line.get('Attributes',False) 
            attribute_values= line.get('Attribute_values',False)
            product_code = line.get('Product_code',False)
            weight = line.get('Weight',False)
            price = line.get('Price',False)
            barcode = line.get('Barcode',False)
            image_url= line.get('Image_url',False)
            category = line.get('Category',False)
            title = line.get('Title',False)
            tags = line.get('Tags',False)
            
            if not main_product_id :
                missing_values.append('main_product_id')
            if not product_code :
                missing_values.append('product_code')
            if not title :
                missing_values.append('title')
            if missing_values :
                transaction_log_obj.create({'job_id':job.id
                                            ,'message' : """ Missing Field(s) Values for %s at Raw Number %s. File - %s"""%(str(missing_values)[1:-1],row_num,server_filename)})
                row_num =  row_num + 1
                continue
            row_num =  row_num + 1  
            dropship_main_product_id = dropship_product_ept_obj.search([('main_product_id','=',main_product_id)],limit=1)
            if partner_id.search_by_vendor_code:
                if not dropship_main_product_id :
                    dropship_main_product_id = dropship_product_ept_obj.create({'main_product_id':main_product_id,
                                                                                'name':title,
                                                                                'partner_id':partner_id.id,
                                                                                'filename':server_filename,
                                                                                })
                    dropship_product_line_ept_obj.create({'dropship_order_id':dropship_main_product_id.id,
                                                         'name':title,
                                                         'vendor_code':product_code,
                                                         'description':description,
                                                         'attribute_name':attributes,
                                                         'attribute_value':attribute_values,
                                                         'price':price,
                                                         'category':category,
                                                         'barcode':barcode,
                                                         'image_url':image_url,
                                                         'weight':weight,
                                                         'tags':tags,
                                                        })
                    created_product = created_product +1
                    transaction_log_obj.create({'job_id':job.id,
                                                'message' : """Primary Data For Product %s Created. Product - %s. File - %s"""%(product_code,title,server_filename)})
                else :
                    dropship_product_line_id = dropship_product_line_ept_obj.search([('vendor_code','=',product_code)],limit=1)
                    if dropship_product_line_id :
                        dropship_product_line_id.write({
                                                         'description':description,
                                                         'name':title,
                                                         'attribute_name':attributes,
                                                         'attribute_value':attribute_values,
                                                         'price':price,
                                                         'category':category,
                                                         'barcode':barcode,
                                                         'image_url':image_url,
                                                         'weight':weight,
                                                         'tags':tags,
                                                         })
                        updated_product = updated_product + 1
                        transaction_log_obj.create({'job_id':job.id,
                                                    'message' : """Primary Data For Product %s Updated. Product - %s. File - %s"""%(product_code,title,server_filename)
                                                    })
                    else:
                        dropship_product_line_id = dropship_product_line_ept_obj.create({'dropship_order_id':dropship_main_product_id.id,
                                                                                         'name':title,
                                                                                         'vendor_code':product_code,
                                                                                         'description':description,
                                                                                         'attribute_name':attributes,
                                                                                         'attribute_value':attribute_values,
                                                                                         'price':price,
                                                                                         'category':category,
                                                                                         'barcode':barcode,
                                                                                         'image_url':image_url,
                                                                                         'weight':weight,
                                                                                         'tags':tags,
                                                                                         })
                        created_product = created_product +1
                        transaction_log_obj.create({'job_id':job.id,
                                                    'message' : """Primary Data For Product %s Created. Product - %s. File - %s"""%(product_code,title,server_filename)
                                                    })
            else:
                if not dropship_main_product_id :
                    dropship_main_product_id = dropship_product_ept_obj.create({'main_product_id':main_product_id,
                                                                                'name':title,
                                                                                'partner_id':partner_id.id,
                                                                                'filename':server_filename,
                                                                                })
                    dropship_product_line_ept_obj.create({'dropship_order_id':dropship_main_product_id.id,
                                                         'name':title,
                                                         'default_code':product_code,
                                                         'description':description,
                                                         'attribute_name':attributes,
                                                         'attribute_value':attribute_values,
                                                         'price':price,
                                                         'category':category,
                                                         'barcode':barcode,
                                                         'image_url':image_url,
                                                         'weight':weight,
                                                         'tags':tags,
                                                        })
                    created_product = created_product +1
                    transaction_log_obj.create({'job_id':job.id,
                                                'message' : """Primary Data For Product %s Created. Product - %s. File - %s"""%(product_code,title,server_filename)
                                                })
                else :
                    dropship_product_line_id = dropship_product_line_ept_obj.search([('default_code','=',product_code)],limit=1)
                    if dropship_product_line_id :
                        dropship_product_line_id.write({
                                                         'description':description,
                                                         'name':title,
                                                         'attribute_name':attributes,
                                                         'attribute_value':attribute_values,
                                                         'price':price,
                                                         'category':category,
                                                         'barcode':barcode,
                                                         'image_url':image_url,
                                                         'weight':weight,
                                                         'tags':tags,
                                                         })
                        updated_product = updated_product + 1
                        transaction_log_obj.create({'job_id':job.id,
                                                    'message' : """Primary Data For Product %s Updated. Product - %s. File - %s"""%(product_code,title,server_filename)
                                                    })
                    else:
                        dropship_product_line_id = dropship_product_line_ept_obj.create({'dropship_order_id':dropship_main_product_id.id,
                                                                                        'name':title,
                                                                                         'default_code':product_code,
                                                                                         'description':description,
                                                                                         'attribute_name':attributes,
                                                                                         'attribute_value':attribute_values,
                                                                                         'price':price,
                                                                                         'category':category,
                                                                                         'barcode':barcode,
                                                                                         'image_url':image_url,
                                                                                         'weight':weight,
                                                                                         'tags':tags,
                                                                                         })
                        created_product = created_product +1
                        transaction_log_obj.create({'job_id':job.id
                                                    ,'message' : """Primary Data For Product %s Created. Product - %s. File - %s"""%(product_code,title,server_filename)
                                                    }) 
        transaction_log_obj.create({'job_id':job.id,
                                    'message' : """Total Created/Updated Products.
                                            ||Total Created - %s
                                            ||Total Updated - %s
                                            ||File - %s"""
                                            %(created_product,updated_product,server_filename)
                                    })
        file = open(filename)
        file.seek(0)
        file_data = file.read().encode()
        if file_data:
            vals = {
                    'name':filename,
                    'datas':base64.encodestring(file_data),
                    'datas_fname':server_filename,
                    'type':'binary',
                    'res_model': 'dropship.file.process.job.ept',
                    }
        attachment=self.env['ir.attachment'].create(vals)
        job.message_post(body=_("<b>Imported supplier's Product File</b>"),attachment_ids=attachment.ids)
        
        # Move To Archive
        try:
            with partner_id.get_dropship_edi_interface(operation="product_import") as dropship_tpw_interface:
                dropship_tpw_interface.archive_file([server_filename])
        except Exception as e:
            transaction_log_obj.create({'job_id':job.id,
                                        'message' : """"Supplier %s has Problem with connection or file Path. File can not Move to Archive."""%(partner_id.name)
                                        })
        return True              

                        
    @api.multi
    def validate_fields(self, fieldnames,job,server_filename):
        '''
            This import pattern requires few fields default, so check it first whether it's there or not.
        '''
        headers = ['Main_product_id','Price','Category','Tags','Description','Attributes','Attribute_values','Product_code','Image_url','Barcode','Weight','Title']
        missing = []
        transaction_log_obj=self.env['dropship.transaction.log.ept']
        for field in headers:
            if field not in fieldnames:
                missing.append(field)
        if len(missing) > 0:
            transaction_log_obj.create({'job_id':job.id
                                        ,'message' : """Header %s is required to Import Products. ||File - %s """%(missing,server_filename)
                                        })
            return False
        return True
    
    @api.multi
    def import_products_from_ftp(self,partner_ids):
        for partner_id in partner_ids:
            transaction_log_obj=self.env['dropship.transaction.log.ept']
            server_filenames=[]
            filenames=[]
            date_time = datetime.now()
            job_filename = "%s_%s" %(partner_id.prefix_allow_import_product or "Import_Products",date_time.strftime('%Y%m%d%H%M%S.csv'))
            job=self.env['dropship.file.process.job.ept'].create({
                                        'application':'product',
                                        'operation_type':'import',
                                        'partner_id':partner_id.id,
                                        'filename':job_filename})
            try:
                with partner_id.get_dropship_edi_interface(operation="product_import") as dropship_edi_object:
                    filenames,server_filenames = dropship_edi_object.pull_from_ftp(partner_id.prefix_allow_import_product)
            except Exception as e:
                transaction_log_obj.create({'job_id':job.id,
                                            'message' : """"Supplier %s has Problem with FTP connection, Please check credentials and file paths.""" %(partner_id.name)
                                            })
                continue
            if not filenames:
                job.unlink()
            for filename,server_filename in zip(filenames,server_filenames):
                reader = csv.DictReader(open(filename,"rU"), delimiter=partner_id.csv_delimiter) 
                fieldnames=reader.fieldnames
                valid_fields=self.validate_fields(fieldnames,job,server_filename)
                if not valid_fields:
                    continue
                self.validate_data(reader,job,partner_id,server_filename,filename)
        return True
    
    @api.multi
    def import_inventory_stock_from_ftp(self,partner_ids,is_cron=False):
        transaction_log_obj=self.env['dropship.transaction.log.ept']
        product_obj=self.env['product.product']
        product_supplierinfo_obj = self.env['product.supplierinfo']
        
        for partner_id in partner_ids:
            server_filenames=[]
            filenames=[]
            try:
                with partner_id.get_dropship_edi_interface(operation="stock_import") as dropship_edi_object:
                    filenames,server_filenames= dropship_edi_object.pull_from_ftp(partner_id.prefix_import_stock)
            except:
                import_time = datetime.now()
                job_filename = "%s_%s" %(partner_id.prefix_import_stock or "Import_Stock",import_time.strftime('%Y%m%d%H%M%S.csv'))
                job=self.env['dropship.file.process.job.ept'].create({
                                            'application':'invenotry',
                                            'operation_type':'import',
                                            'partner_id':partner_id.id,
                                            'filename':job_filename,
                                            'message':"Problem with connection or file Path.Please check credentials and file paths.",
                                            })
                continue
            for filename,server_filename in zip(filenames,server_filenames):
                row_num = 1
                export_time = datetime.now()
                job_filename = "%s_%s" %(partner_id.prefix_import_stock or "Import_Stock",export_time.strftime('%Y%m%d%H%M%S.csv'))
                job=self.env['dropship.file.process.job.ept'].create({
                                            'application':'invenotry',
                                            'operation_type':'import',
                                            'partner_id':partner_id.id,
                                            'filename':job_filename})
                reader = csv.DictReader(open(filename,"rU"), delimiter=partner_id.csv_delimiter) 
                fieldnames=reader.fieldnames
                headers = ['sku','quantity']
                missing = []
                for field in headers:
                    if field not in fieldnames:
                        missing.append(field)
                if len(missing) > 0:
                    transaction_log_obj.create({'job_id':job.id,
                                                'message' : """ %s  is required field to Import Stock. File - %s """%(missing,server_filename)
                                                })
                    continue
                for line in reader:
                    product_sku = line.get('sku')
                    product_qty = 0.0
                    if line.get('quantity'):
                        product_qty = float(line.get('quantity'))
                    if product_sku:
                        product_id = product_obj.search([('default_code','=',product_sku)],limit=1)
                        if not product_id:
                            vendor_product_id = product_supplierinfo_obj.search([('product_code','=',product_sku),('name','=',partner_id.id)],limit=1)
                            if vendor_product_id:
                                vendor_product_id.write({'vendor_product_qty':product_qty})
                                transaction_log_obj.create({'job_id':job.id
                                                            ,'message' : "Quantity %s Updated Successfully for SKU Product %s"%(product_qty,product_sku)
                                                            })
                                row_num =  row_num + 1
                            if not vendor_product_id:
                                transaction_log_obj.create({'job_id':job.id
                                                            ,'message' : "Product %s for %s Supplier not available in Odoo"%(product_sku,partner_id.name)
                                                            })
                                row_num =  row_num + 1
                                continue
                        else:
                            vendor_product_id = product_supplierinfo_obj.search([('product_id','=',product_id.id),('name','=',partner_id.id)])
                            if vendor_product_id :
                                vendor_product_id.write({'vendor_product_qty':product_qty})
                                transaction_log_obj.create({'job_id':job.id
                                                            ,'message' : "Quantity %s Updated Successfully for SKU Product %s"%(product_qty,product_sku)
                                                            })
                                row_num =  row_num + 1
                            else:
                                transaction_log_obj.create({'job_id':job.id
                                                            ,'message' : "Product %s for %s Supplier not available in Odoo"%(product_sku,partner_id.name)
                                                            })
                                row_num =  row_num + 1
                                continue
                    else:
                        missing_value = 'sku'
                        transaction_log_obj.create({'job_id':job.id,
                                                    'message' : """ Missing Field(s) Value for %s at Raw Number %s. File - %s"""%(missing_value,row_num,server_filename)
                                                    })
                        row_num =  row_num + 1
                        continue
                file = open(filename)
                file.seek(0)
                file_data = file.read().encode()
                if file_data:
                    vals = {
                            'name':filename,
                            'datas':base64.encodestring(file_data),
                            'datas_fname':server_filename,
                            'type':'binary',
                            'res_model': 'dropship.file.process.job.ept',
                            }
                attachment=self.env['ir.attachment'].create(vals)
                job.message_post(body=_("<b>Inventory Stock Imported File</b>"),attachment_ids=attachment.ids)
                
                # Move To Archive
                try:
                    with partner_id.get_dropship_edi_interface(operation="stock_import") as dropship_tpw_interface:
                        dropship_tpw_interface.archive_file([server_filename])
                except:
                    job.write({'message': "Problem with connection or file Path. File can not Move to Archive."})
                
        return True
    
    @api.model                    
    def auto_import_inventory_stock_from_ftp(self,ctx={}):
        partner_obj=self.env['res.partner']
        if not isinstance(ctx,dict) or not 'partner_id' in ctx:
            return True
        partner_id = ctx.get('partner_id',False)
        partner_ids = partner_obj.browse(partner_id)
        if partner_ids:
            self.import_inventory_stock_from_ftp(partner_ids,is_cron=True)
        return True
    
    @api.model
    def auto_import_products_from_ftp(self,ctx={}):
        partner_obj=self.env['res.partner']
        if not isinstance(ctx,dict) or not 'partner_id' in ctx:
            return True
        partner_id = ctx.get('partner_id',False)
        partner_ids = partner_obj.browse(partner_id)
        if partner_ids:
            self.import_products_from_ftp(partner_ids)
        return True
                        