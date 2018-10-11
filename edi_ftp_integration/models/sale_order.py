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

class SaleOrder(models.Model):
    
    _inherit="sale.order"

    picking_ref = fields.Char(string="Picking Reference")
    
    @api.multi
    def already_imported_order(self,partner,file_order_number,file_picking_ref):
        sale_order = self.search([('partner_id','=',partner.id),('picking_ref','=',file_picking_ref),('client_order_ref','=',file_order_number)],limit=1)
        return sale_order
    
    @api.model
    def process_delivery_address(self,data):
        company = False
        if data.get('company_name',False):
            company = self.env['res.partner'].search([('name','=',data.get('company_name')),('is_company','=',True)],limit=1)
         
        street = "%s, %s"%(data.get('house_no',''),data.get('street1','')) if data.get('house_no',False) else data.get('street1','') 
        final_data = {
            'company': company and company.id or False,
            'name': "%s %s"%(data.get('first_name',''),data.get('last_name','')),
            'street': street,
            'street2': data.get('street2',''),
            'phone': data.get('contact_no',''),
            'email_id': data.get('email',''),
            'city': data.get('city',''),
            'postal-code': data.get('zip',''),
            'country_name': data.get('country',''),
            'state_name' : data.get('state',''),
        }
        delivery_address = self.env['res.partner'].create_or_update_partner(final_data)
        return delivery_address
        
    @api.model
    def prepare_sale_order_data(self,data):
        sale_order = self.env['sale.order']
        fpos = False
        order_vals = {
            'picking_ref':data.get('picking_ref',False),
            'name':data.get('name',False),
            'partner_id' :data.get('partner_id'),
            'partner_shipping_id' : data.get('partner_shipping_id'),
            'warehouse_id' : data.get('warehouse_id'),
            'company_id':data.get('company_id'),
        }
        new_record = sale_order.new(order_vals)
        new_record.onchange_partner_id() # Return Pricelist- Payment terms- Invoice address- Delivery address
        new_record.onchange_partner_id_carrier_id()
        new_record.onchange_partner_shipping_id() # Return Fiscal Position
        order_vals = sale_order._convert_to_write({name: new_record[name] for name in new_record._cache})
        fpos = order_vals.get('fiscal_position_id',fpos)
        order_vals.update({
            'picking_ref':data.get('picking_ref',False),
            'name':data.get('name',False),
            'partner_id' :data.get('partner_id'),
            'partner_shipping_id' : data.get('partner_shipping_id'),
            'warehouse_id' : data.get('warehouse_id'),
            'company_id':data.get('company_id'),
            'fiscal_position_id': fpos,
            'client_order_ref':data.get('client_order_ref',''),
            })
            
        return order_vals
        
    @api.model
    def import_sale_orders_from_ftp(self,partner_ids=[],is_cron=False):
        
        if not partner_ids:
            partner_ids = self.env['res.partner'].search([('integrate_edi','=',True)])
        
        for partner in partner_ids:
            
            if not partner.integrate_edi:
                continue
            
            server_filenames = False
            filenames = False
            with partner.get_edi_interface(operation="sale_import") as edi_interface:
                if partner.prefix_sale_import:
                    filenames, server_filenames = \
                        edi_interface.pull_from_ftp(partner.prefix_sale_import)
                else:
                    filenames, server_filenames = \
                        edi_interface.pull_from_ftp('sale_order')
            
            jobs_to_process = []  
            for file_count in range(0,len(filenames)):
                with open(filenames[file_count]) as file:
                    header = True
                    file_process_obj=self.env['edi.file.process.job']        
                    transaction_log_obj=self.env['edi.transaction.log']
                    job_id = False
                    for line in UnicodeDictReader(file,['order_no','picking_ref','sku','quantity','company_name','first_name','last_name','street1','street2','country','state','city','zip','email','contact_no','house_no'], delimiter=partner.csv_delimiter):
                        if header:
                            header = False
                            continue
                        if not job_id:
                            job_id=file_process_obj.create({
                                'application':'sales',
                                'ftp_partner_id':partner.id,
                                'operation_type':'import',
                                'filename':server_filenames[file_count],
                            })
                            jobs_to_process.append(job_id)
                           
                        if not ( line.get('first_name',False) or line.get('last_name',False) ):
                            transaction_log_obj.create({
                            'file_order_number':line.get('order_no'),
                            'file_picking_ref':line.get('picking_ref'),
                            'file_quantity':line.get('quantity'),
                            'file_sku':line.get('sku'),
                            'job_id':job_id.id,
                            'is_processed':False,
                            'Message' : "First name and Last Name of customer is required to process order"
                            })
                            continue
                            
                        delivery_address = self.process_delivery_address(line)
                        
                        transaction_log_obj.create({
                            'file_order_number':line.get('order_no'),
                            'file_quantity':line.get('quantity'),
                            'file_picking_ref':line.get('picking_ref'),
                            'file_sku':line.get('sku'),
                            'delivery_address_id':delivery_address.id,
                            'job_id':job_id.id,
                            'is_processed':False
                        })
                    file.seek(0)
                    file_data = file.read().encode()
                    vals = {
                            'name':server_filenames[file_count],
                            'datas':base64.encodestring(file_data),
                            'datas_fname':filenames[file_count],
                            'type':'binary',
                            'res_model':'edi.file.process.job',
                            }
                    attachment=self.env['ir.attachment'].create(vals)
                    job_id.message_post(body=("<b>Sales file imported</b>"),attachment_ids=attachment.ids)

            for job in jobs_to_process:
                job.process_sale_orders()
                
            # Move To Archive
            try:
                with partner.get_edi_interface(operation="sale_import") as tpw_interface:
                    tpw_interface.archive_file(server_filenames)
                    tpw_interface.delete_from_tmp(filenames)
            except:
                if is_cron:
                    job.write({'message': "Problem with moveing file to Archive Directory."})
                else:
                    raise Warning("Problem with moving file to Archive Directory. Please check credentials and file paths")