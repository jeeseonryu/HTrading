from odoo import api, fields, models, _
from io import StringIO
from datetime import datetime
import base64
from csv import DictWriter
from odoo.exceptions import Warning
import csv
from .api import UnicodeDictWriter,UnicodeDictReader

class Picking(models.Model):
    _inherit = "stock.picking"
    
    is_exported = fields.Boolean(string="is exported?",default=False)
    
    @api.multi
    def import_shipment_details_from_ftp(self,partner_ids):
        transaction_log_obj = self.env['dropship.transaction.log.ept']
        for partner_id in partner_ids:
            validate_picking_ids = []
            server_filenames=[]
            filenames=[]
            try:
                with partner_id.get_dropship_edi_interface(operation="shipment_import") as dropship_edi_object:
                    filenames,server_filenames= dropship_edi_object.pull_from_ftp(partner_id.prefix_shipment_tracking)
            except:
                import_time = datetime.now()
                job_filename = "%s_%s" %(partner_id.prefix_shipment_tracking or "shipment_imports",import_time.strftime('%Y%m%d%H%M%S.csv'))
                job=self.env['dropship.file.process.job.ept'].create({
                                            'application':'shipment',
                                            'operation_type':'import',
                                            'partner_id':partner_id.id,
                                            'filename':job_filename,
                                            'message':"Problem with connection or file Path.Please check credentials and file paths.",
                                            })
                continue
            
            for filename,server_filename in zip(filenames,server_filenames):
                row_num = 1
                import_time = datetime.now()
                job_filename = "%s_%s" %(partner_id.prefix_shipment_tracking or "shipment_imports",import_time.strftime('%Y%m%d%H%M%S.csv'))
                job=self.env['dropship.file.process.job.ept'].create({
                                            'application':'shipment',
                                            'operation_type':'import',
                                            'partner_id':partner_id.id,
                                            'filename':job_filename})
                reader = csv.DictReader(open(filename,"rU"), delimiter=partner_id.csv_delimiter) 
                fieldnames=reader.fieldnames
                headers = ['order_no','picking_ref','sku','quantity','tracking_no']
                missing = []
                for field in headers:
                    if field not in fieldnames:
                        missing.append(field)
                if len(missing) > 0:
                    transaction_log_obj.create({'job_id':job.id
                                                ,'message' : """ %s is required field to Import Shipment Details. File - %s """%(str(missing)[1:-1],server_filename)
                                                })
                    continue
                skip_purchase_order_ids = self.check_mismatch_details_for_import_shipment(partner_id,server_filename,job,reader)
                reader = csv.DictReader(open(filename,"rU"), delimiter=partner_id.csv_delimiter)
                for line in reader:
                    order_ref = line.get('picking_ref') or ''
                    order_no = line.get('order_no') or ''
                    product_sku = line.get('sku') or ''
                    product_qty = 0.0
                    if line.get('quantity'):
                        product_qty = float(line.get('quantity'))
                    tracking_no = line.get('tracking_no') or ''
                    stock_pickng_id =self.search([('name','=',order_ref),('state','not in',['done','cancel'])],limit=1)
                    if stock_pickng_id in list(set(skip_purchase_order_ids)):
                        continue
                    product_vendorcode_id = self.env['product.supplierinfo'].search([('product_code','=',product_sku)],limit=1)
                    if product_vendorcode_id:
                        stock_move_id = self.env['stock.move'].search([('product_id','=',product_vendorcode_id.product_id.id),('origin','=',stock_pickng_id.origin)],limit=1)
                        if stock_move_id:
                            if stock_move_id.product_uom_qty < float(product_qty) :
                                transaction_log_obj.create({'job_id':job.id
                                                            ,'message' : """Product %s Ordered Quantity %s Shipped Quantity %s. Order_no - %s. File - %s"""%(product_vendorcode_id.product_id.name,stock_move_id.product_uom_qty,product_qty,order_no,server_filename)
                                                            })
                            stock_move_id.move_line_ids.write({'qty_done':product_qty})
                            validate_picking_ids.append(stock_move_id.picking_id)
                            if tracking_no:
                                if stock_move_id.picking_id.carrier_tracking_ref:
                                    stock_move_id.picking_id.write({'carrier_tracking_ref':str('%s,%s'%(stock_move_id.picking_id.carrier_tracking_ref,tracking_no))})
                                else:
                                    stock_move_id.picking_id.write({'carrier_tracking_ref':tracking_no})
                    else:
                        product_id = self.env['product.product'].search([('default_code','=',product_sku)],limit=1)
                        if product_id:
                            stock_move_id = self.env['stock.move'].search([('product_id','=',product_id.id),('origin','=',stock_pickng_id.origin)],limit=1)
                            if stock_move_id:
                                if stock_move_id.product_uom_qty < float(product_qty) :
                                    transaction_log_obj.create({'job_id':job.id
                                                                ,'message' : """Product %s Ordered Quantity %s Shipped Quantity %s. Order_no - %s. File - %s."""%(product_id.name,stock_move_id.product_uom_qty,product_qty,order_no,server_filename)
                                                                })
                                stock_move_id.move_line_ids.write({'qty_done':product_qty})
                                validate_picking_ids.append(stock_move_id.picking_id)
                                if tracking_no:
                                    if stock_move_id.picking_id.carrier_tracking_ref:
                                        stock_move_id.picking_id.write({'carrier_tracking_ref':str('%s,%s'%(stock_move_id.picking_id.carrier_tracking_ref,tracking_no))})
                                    else:   
                                        stock_move_id.picking_id.write({'carrier_tracking_ref':tracking_no})
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
                job.message_post(body=_("<b>Imported Shipment's File</b>"),attachment_ids=attachment.ids)
                
                if server_filename:
                    try:
                        with partner_id.get_dropship_edi_interface(operation="shipment_import") as dropship_tpw_interface:
                            dropship_tpw_interface.archive_file([server_filename])
                    except:
                        job.write({'message': "Problem with connection or file Path. File can not Move to Archive Directory."})
                
            for validate_picking_id in list(set(validate_picking_ids)):
                validate_picking_id.action_done()
                transaction_log_obj.create({'job_id':job.id
                                            ,'message' : """Dropship Order Validated Successfully. Dropship Order - %s. File - %s."""%(validate_picking_id.origin,server_filename)
                                            }) 
        return True             
    
    @api.multi
    def export_orders_detail_to_ftp(self,pickings=False,partner_ids=False,is_cron=False):
        transaction_log_obj = self.env['dropship.transaction.log.ept']
        for partner_id in partner_ids:
            picking_ids = self.search([('partner_id', '=', partner_id.id),('id', 'in', pickings.ids)])
            
            if picking_ids:
                # Start CSV Writer
                buffer = StringIO()
                field_names = ['order_no','picking_ref','sku','quantity','company_name','first_name','last_name','street1','street2'
                               ,'country','state','city','zip','email','contact_no','house_no']
                
                export_time = datetime.now()
                filename = "%s_%s" %(partner_id.prefix_allow_shipment_export or "Export_Picking",export_time.strftime('%Y%m%d%H%M%S.csv'))
                job = self.env['dropship.file.process.job.ept'].create({'application':'shipment'
                                                                        ,'operation_type':'export',
                                                                        'partner_id':partner_id.id,
                                                                        'filename':filename
                                                                        })
                csvwriter = DictWriter(buffer, field_names, delimiter=partner_id.csv_delimiter or ';')
                csvwriter.writer.writerow(field_names)
                for picking_id in picking_ids:
                    missmatch = self.check_mismatch_details_for_dropship_orders(partner_id,picking_id,picking_id.move_lines,filename,job)
                    if missmatch:
                        continue
                    for move_line in picking_id.move_lines:
                        product_supplier_id = self.env['product.supplierinfo'].search([('product_id','=',move_line.product_id.id),('name','=',partner_id.id)],limit=1)
                        if product_supplier_id.product_code:
                            product_code = product_supplier_id.product_code
                        elif move_line.product_id.default_code:
                            product_code = move_line.product_id.default_code
                        
                        data = {
                                'order_no':picking_id.purchase_id.name,
                                'picking_ref':picking_id.name,
                                'sku':product_code,
                                'quantity':move_line.product_uom_qty,
                                'company_name':picking_id.sale_id.partner_shipping_id.company_id.name or '',
                                'first_name':picking_id.sale_id.partner_shipping_id.name,
                                'last_name':'',
                                'street1':picking_id.sale_id.partner_shipping_id.street,
                                'street2':picking_id.sale_id.partner_shipping_id.street2 or '',
                                'country':picking_id.sale_id.partner_shipping_id.country_id.name,
                                'state':picking_id.sale_id.partner_shipping_id.state_id.name,
                                'city':picking_id.sale_id.partner_shipping_id.city,
                                'zip':picking_id.sale_id.partner_shipping_id.zip,
                                'email':picking_id.sale_id.partner_shipping_id.email or '',
                                'contact_no':picking_id.sale_id.partner_shipping_id.mobile or picking_id.sale_id.partner_shipping_id.phone or '',
                                'house_no':'',
                                }
                        csvwriter.writerow(data)
                        transaction_log_obj.create({'job_id':job.id
                                                    ,'message' : """Dropship Order %s Exported Succesfully. Sale Order - %s. Product - %s"""%(picking_id.purchase_id.name,picking_id.sale_id.name,move_line.product_id.name)
                                                    })
                try:
                    with partner_id.get_dropship_edi_interface(operation="shipment_export") as dropship_tpw_interface:
                        buffer.seek(0)
                        dropship_tpw_interface.push_to_ftp(filename, buffer)
                except Exception as e:
                    job.write({'message': "Problem with connection or file Path. File not exported to Partner's FTP."})
                
                if not job.transaction_log_ids and not job.message:
                    picking_id.write({'is_exported':True})
                    transaction_log_obj.create({'job_id':job.id
                                                ,'message' : """File Exported Successfully."""
                                                })
                buffer.seek(0)
                file_data = buffer.read().encode()
                if file_data:
                    vals = {
                            'name':filename,
                            'datas':base64.encodestring(file_data),
                            'datas_fname':filename,
                            'type':'binary',
                            'res_model': 'dropship.file.process.job.ept',
                            }
                    attachment=self.env['ir.attachment'].create(vals)
                    job.message_post(body=_("<b>Purchase Order Exported File</b>"),attachment_ids=attachment.ids)
                    buffer.close()
        return True
    
    @api.multi
    def check_mismatch_details_for_import_shipment(self,partner_id,server_filename,job,data):
        transaction_log_obj = self.env['dropship.transaction.log.ept']
        missing_values = []
        skip_purchase_order_ids=[]
        row_num = 1
        for line in data:
            order_no = line.get('order_no') or ''
            order_ref = line.get('picking_ref')  or ''
            stock_picking_id =self.search([('name','=',order_ref),('state','not in',['done','cancel'])],limit=1)
            done_stock_picking_id =self.search([('name','=',order_ref),('state','=','done')],limit=1)
            cancel_stock_picking_id =self.search([('name','=',order_ref),('state','=','cancel')],limit=1)
            product_sku = line.get('sku') or ''
            product_qty = line.get('quantity') or ''
            tracking_no = line.get('tracking_no') or ''
            
            if not order_ref:
                missing_values.append('picking_ref')
            if not order_no:
                missing_values.append('order_no')
            if not product_sku:
                missing_values.append('sku')
            if not product_qty:
                missing_values.append('quantity')
            if not tracking_no:
                missing_values.append('tracking_no')
            if missing_values:
                transaction_log_obj.create({'job_id':job.id
                                            ,'message' : """ Missing Field Value for %s at Raw Number %s. File - %s"""%(str(missing_values)[1:-1],row_num,server_filename)
                                            })
                row_num =  row_num + 1
                skip_purchase_order_ids.append(stock_picking_id.id)
                continue
            
            if done_stock_picking_id:
                transaction_log_obj.create({'job_id':job.id
                                            ,'message' : """This Order No. %s already Processed. Dropship Order Ref. - %s. File - %s"""%(order_ref,order_no,server_filename)
                                            })
                row_num =  row_num + 1
                skip_purchase_order_ids.append(done_stock_picking_id.id)
                continue
            
            if cancel_stock_picking_id:
                transaction_log_obj.create({'job_id':job.id
                                            ,'message' : """This order no %s is cancelled state. Dropship Order Ref. - %s. File - %s"""%(order_ref,order_no,server_filename)
                                            })
                row_num =  row_num + 1
                skip_purchase_order_ids.append(cancel_stock_picking_id.id)
                continue
            
            if stock_picking_id:
                product_vendorcode_id = self.env['product.supplierinfo'].search([('product_code','=',product_sku)],limit=1)
                product_id = self.env['product.product'].search([('default_code','=',product_sku)],limit=1)
                if not product_vendorcode_id and not product_id:
                    transaction_log_obj.create({'job_id':job.id
                                                ,'message' : """Product %s not  found in odoo. File - %s"""%(product_sku,server_filename)
                                                })
                    row_num =  row_num + 1
                    skip_purchase_order_ids.append(cancel_stock_picking_id.id)
                    continue
            else:   
                transaction_log_obj.create({'job_id':job.id
                                            ,'message' : """There is no Dropship order like %s in Odoo. Order No. - %s. File - %s """%(order_ref,order_no,server_filename)
                                            })
                row_num =  row_num + 1
                skip_purchase_order_ids.append(cancel_stock_picking_id.id)
                continue
            row_num =  row_num + 1
        return skip_purchase_order_ids
    
    @api.multi
    def check_mismatch_details_for_dropship_orders(self,partner_id,picking_id,move_lines,filename,job):
        transaction_log_obj = self.env['dropship.transaction.log.ept']
        missmatch = False
        missing_values = []
        order_no = picking_id.purchase_id.name
        first_name = picking_id.sale_id.partner_shipping_id.name or ''
        street1 = picking_id.sale_id.partner_shipping_id.street
        country = picking_id.sale_id.partner_shipping_id.country_id.name or ''
        state = picking_id.sale_id.partner_shipping_id.state_id.name or ''
        city = picking_id.sale_id.partner_shipping_id.city or ''
        zip = picking_id.sale_id.partner_shipping_id.zip or ''
        
        if not first_name:
            missing_values.append('first_name')
        if not street1:
            missing_values.append('street1')
        if not country:
            missing_values.append('country')
        if not state:
            missing_values.append('state')
        if not city:
            missing_values.append('city')
        if not zip:
            missing_values.append('zip')
        if missing_values :
            transaction_log_obj.create({'job_id':job.id
                                        ,'message' : """Dropship Order %s Skipped Due to this mandatory field(s) %s Value not inserted. Sale_order - %s """%(order_no,missing_values,picking_id.sale_id.name)
                                        })
            missmatch = True
                    
        for move_line in picking_id.move_lines:
            product_supplier_id = self.env['product.supplierinfo'].search([('product_id','=',move_line.product_id.id),('name','=',partner_id.id)],limit=1)
            if product_supplier_id.product_code:
                product_supplier_id.product_code
            elif move_line.product_id.default_code:
                move_line.product_id.default_code
            else:
                transaction_log_obj.create({'job_id':job.id
                                            ,'message' : """Dropship Order %s Skipped Due to Product not found in Odoo Product. Product - %s"""%(order_no,move_line.product_id.name)
                                            })
                missmatch = True
        return missmatch
    
    @api.multi
    def auto_export_orders_detail_to_ftp(self,ctx={}):
        partner_obj = self.env['res.partner']
        stock_picking_obj = self.env['stock.picking']
        if not isinstance(ctx,dict) or not 'partner_id' in ctx:
            return True
        partner_id = ctx.get('partner_id',False)
        partner_ids = partner_obj.browse(partner_id)
        picking_ids = stock_picking_obj.search([('picking_type_id.is_dropship_process','=',True),('partner_id','in',partner_ids.ids),('state','not in',('cancel','done')),('is_exported','!=',True)])
        if partner_ids and picking_ids:
            self.export_orders_detail_to_ftp(picking_ids, partner_ids,is_cron=True)
        return True
    
    @api.multi
    def auto_import_shipment_details_from_ftp(self,ctx={}):
        partner_obj = self.env['res.partner']
        if not isinstance(ctx,dict) or not 'partner_id' in ctx:
            return True
        partner_id = ctx.get('partner_id',False)
        partner_ids = partner_obj.browse(partner_id)
        if partner_ids:
            self.import_shipment_details_from_ftp(partner_ids)
        return True