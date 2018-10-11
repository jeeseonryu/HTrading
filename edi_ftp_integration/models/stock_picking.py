from odoo import models,fields,api, _
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

class StockPicking(models.Model):
    
    _inherit="stock.picking"
    
    is_exported_to_partner_ftp = fields.Boolean("Is Exported")
    client_order_ref = fields.Char(string="Client Order Ref",related='sale_id.client_order_ref')
    ftp_partner_id = fields.Many2one('res.partner',related='sale_id.partner_id')
    
    @api.model
    def _export_tracking_details_to_partner_ftp(self,partner_ids=False,is_cron=False):
        
        if not partner_ids:
            partner_ids = self.env['res.partner'].search([('integrate_edi','=',True),('allow_shipment_export','=',True)])
        
        transaction_log_obj=self.env['edi.transaction.log']
        picking = self.search([('state','=','done'),('is_exported_to_partner_ftp','=',False)])
        for partner in partner_ids:
            
            if not partner.allow_shipment_export:
                continue
            
            partner_pickings = picking.filtered(lambda x: x.ftp_partner_id.id == partner.id)
            
            # Start CSV Writer
            buffer = StringIO()
            field_names = [
                'order_no',
                'picking_ref',
                'sku',
                'quantity',
                'tracking_no',
            ]
            
            export_time = datetime.now()
            filename = "%s_%s" %(partner.prefix_shipment_export or "Export_Trackings",export_time.strftime('%Y%m%d%H%M%S.csv'))
            job=self.env['edi.file.process.job'].create({'application':'shipment'
                                             ,'operation_type':'export',
                                             'ftp_partner_id':partner.id,
                                             'filename':filename})
            
            csvwriter = DictWriter(buffer, field_names, delimiter=partner.csv_delimiter or ';')
            #csvwriter = UnicodeDictWriter(buffer, field_names, delimiter=';')
            csvwriter.writer.writerow(field_names)
            for partner_picking in partner_pickings:
                for move_line in partner_picking.move_lines:
                    partner_product = self.env['partner.product.ept'].search([('partner_id','=',partner.id),('product_id','=',move_line.product_id.id)],limit=1)
                    sku = False
                    if not partner_product:
                        sku =  move_line.product_id.default_code
                    else:
                        sku = partner_product.sku
                        
                    data = {
                        'order_no':partner_picking.client_order_ref or partner_picking.sale_id.name,
                        'picking_ref':partner_picking.sale_id.picking_ref or '',
                        'sku':sku,
                        'quantity':move_line.quantity_done,
                        'tracking_no':partner_picking.carrier_tracking_ref or ''
                    }
                    transaction_log_obj.create({
                        'product_id': move_line.product_id.id,
                        'file_quantity': move_line.quantity_done,
                        'file_sku':sku,
                        'sale_order':partner_picking.sale_id and partner_picking.sale_id.id,
                        'file_order_number':partner_picking.client_order_ref,
                        'job_id': job.id,
                        'picking_id':partner_picking.id,
                        'delivery_address_id':partner_picking.partner_id.id,
                        'tracking_no':partner_picking.carrier_tracking_ref,
                        'is_processed': True,
                        'message': "Line Exported"
                    })
                    csvwriter.writerow(data)
                    
                if job.transaction_log_ids:
                    partner_picking.write({'is_exported_to_partner_ftp':True})
            
            try:
                with partner.get_edi_interface(operation="shipment_export") as tpw_interface:
                        buffer.seek(0)
                        tpw_interface.push_to_ftp(filename, buffer)
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
            job.message_post(body=_("<b>Tracking Exported File</b>"),attachment_ids=attachment.ids)
            buffer.close()
        