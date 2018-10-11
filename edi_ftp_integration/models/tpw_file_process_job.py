from odoo import models,fields,api

class edi_file_process_job(models.Model):
    
    _name="edi.file.process.job"
    _description = "EDI Log"
    _inherit = ['mail.thread']

    _order='id desc'
    
    name = fields.Char("Name")
    filename = fields.Char("File Name")
    transaction_log_ids = fields.One2many("edi.transaction.log","job_id",string="Log")
    application = fields.Selection([('sales','Sales')
                                    ,('shipment','Delivery')
                                    ,('invenotry','Inventory')
                                    ,('product','Product')
                                    ,('other','Other')],string="Application")
    operation_type = fields.Selection([('import','Import'),('export','Export')]
                                      ,string="Operation")    
    message=fields.Text("Message")
    company_id=fields.Many2one('res.company',string="Company")
    ftp_partner_id = fields.Many2one('res.partner',string="FTP Partner")
    is_processed = fields.Boolean(string="Is Processed",compute="_is_job_processed")
    
    @api.multi
    def reprocess_job(self):
        for record in self:
            if record.application == 'sales' and record.operation_type == 'import' and not record.is_processed:
                record.process_sale_orders()
        return True
    
    @api.multi
    def _is_job_processed(self):
        for record in self:
            is_processed = True
            for line in record.transaction_log_ids:
                if not line.is_processed:
                    is_processed = False

            record.is_processed = is_processed
            
    @api.model
    def create(self,vals):
        sequence=self.env.ref("edi_ftp_integration.seq_edi_file_process_job")
        name = sequence and sequence.next_by_id() or '/'
        company_id=self._context.get('company_id',self.env.user.company_id.id)
        if type(vals)==dict:
            vals.update({'name':name,'company_id':company_id})
        return super(edi_file_process_job,self).create(vals)

    @api.multi
    def process_sale_orders(self):
        
        for record in self:
            partner = record.ftp_partner_id
            
            order_black_list = []
            for line in record.transaction_log_ids.filtered(lambda r: r.is_processed == False):
                # Improve SKU and Partner Product Mapping Must be there in ERP
                if not line.file_order_number:
                    line.write({
                        'is_processed':False,
                        'message' : "Order Number not mentioned in file"
                    })
                    continue
                
                if not line.delivery_address_id:
                    line.write({
                        'is_processed':False,
                        'message' : "Problem with delivery address. Please create and select delivery address manually"
                    })
                    order_black_list.append(line.file_order_number)
                    continue
                
                if not line.file_sku:
                    line.write({
                        'is_processed':False,
                        'message' : "Sku not mentioned in file"
                    })
                    if line.file_order_number not in order_black_list:
                        order_black_list.append(line.file_order_number)
                    continue
                
#                 partner_product = self.env['partner.product.ept'].search([('partner_id','=',partner.id),('sku','=',line.file_sku)],limit=1)
                partner_product = self.env['product.product'].get_product_from_sku(partner,line.file_sku)
                if not partner_product:
                    line.write({
                        'is_processed':False,
                        'message' : "Product not found with sku %s and partner %s"%(line.file_sku,partner.name)
                    })
                    if line.file_order_number not in order_black_list:
                        order_black_list.append(line.file_order_number)
                    continue

                processed_sale_order = self.env['sale.order'].already_imported_order(partner,line.file_order_number,line.file_picking_ref)
                if processed_sale_order:
                    line.write({
                        'is_processed':False,
                        'message' : "Order No - %s and Picking reference - %s already Imported in Odoo"%(line.file_order_number,line.file_picking_ref)
                    })
                    if line.file_order_number not in order_black_list:
                        order_black_list.append(line.file_order_number)
                    continue
                     
            sale_orders = []
            for line in record.transaction_log_ids.filtered(lambda r: r.is_processed == False):
                
                if not line.file_order_number:
                    line.write({
                        'is_processed':False,
                        'message' : "Order Number not mentioned in file"
                    })
                    continue
                
                if line.file_order_number in order_black_list:
                    continue
                
#                 partner_product = self.env['partner.product.ept'].search([('partner_id','=',partner.id),('sku','=',line.file_sku)],limit=1)
                partner_product = self.env['product.product'].get_product_from_sku(partner,line.file_sku)
                # Sale Order Processing
                sale_order = self.env['sale.order'].search([('partner_id','=',partner.id),('client_order_ref','=',line.file_order_number),('state','=','draft')],limit=1)
                if not sale_order:
                    delivery_address = line.delivery_address_id
                    if not delivery_address:
                        continue
                    
                    # Order Processing Unit
                    warehouse = partner.sale_warehouse_id
                    
                    if not warehouse:
                        # Get warehouse from configuration
                        configuration_record = self.env.ref('edi_ftp_integration.edi_default_configuration')
                        warehouse = configuration_record.order_warehouse_id
                        
                    order_data = {
                        'company_id':warehouse.company_id.id,
                        'warehouse_id':warehouse.id,
                        'picking_ref':line.file_picking_ref,
                        'partner_id': partner.id,
                        'partner_shipping_id':delivery_address.id,
                        'client_order_ref':line.file_order_number,
                    }
                    
                    order_number = False
                    
                    if partner.order_number_from == 'default':
                        configuration = self.env.ref('edi_ftp_integration.edi_default_configuration')
                        if configuration.order_number_from == 'file':
#                             order_number = line.file_order_number
                            name=self.env['ir.sequence'].next_by_code('sale.order')
                            order_data.update({'name':name})
                                                
                    if partner.order_number_from == 'file':
                        order_number = line.file_order_number
                        order_data.update({'name':order_number})
                        
                    if partner.order_number_from == 'prefix_file':
                        order_number = line.file_order_number
                        order_data.update({'name': "%s%s"%(partner.order_number_prefix,order_number)})
                    
                    order_dict = sale_order.prepare_sale_order_data(order_data)
                    if not order_dict.get('name',True):
                        del order_dict['name']
                    sale_order = self.env['sale.order'].create(order_dict)
                
                sale_orders.append(sale_order)
                # Sale Line Processing
                sale_line_obj = self.env['sale.order.line']
                order_line_value = sale_line_obj.create_sale_order_line_dict(partner,partner_product,line.file_quantity,False,sale_order)
#                 order_line_value = sale_line_obj.create_sale_order_line_dict(partner,partner_product.product_id,line.file_quantity,False,sale_order)
                sale_order_line = sale_line_obj.create(order_line_value)
                line.write({
                    'is_processed':True,
                    'product_id':sale_order_line.product_id.id,
                    'sale_order':sale_order.id,
                    'message' : "Line Processed Successfully"
                })
            
            # Run Workflow
            for order in sale_orders:
                autoworkflow = False
                if order.partner_id.auto_workflow_id:
                    autoworkflow = order.partner_id.auto_workflow_id
                else:
                    autoworkflow = self.env.ref('edi_ftp_integration.edi_default_configuration').auto_workflow_id
                
                if not autoworkflow:
                    continue
                
                order.write({'auto_workflow_process_id':autoworkflow.id})
                
                if record.is_processed:
                    try:
                        autoworkflow.auto_workflow_process(ids=[order.id])
                    except:
                        continue

class tpw_transaction_log(models.Model):

    _name = 'edi.transaction.log'
    _rec_name='job_id'
    _order='id desc'
    
    product_id = fields.Many2one('product.product',string="Product")
    file_quantity = fields.Float("Quantity")
    file_sku = fields.Char("File SKU")
    file_order_number = fields.Char("Order Number from file")
    file_picking_ref = fields.Char(string="Picking Reference")
    job_id = fields.Many2one('edi.file.process.job',string="Job")
    sale_order = fields.Many2one('sale.order',string="Sale Order")
    delivery_address_id = fields.Many2one('res.partner',string="Delivery Address")
    picking_id = fields.Many2one('stock.picking',string="Delivery Order")
    tracking_no = fields.Char(string="Tracking No")
    is_processed = fields.Boolean(string="Is Processed",default=False)
    message = fields.Text(string="Message")
    
    @api.model
    def create(self,vals):
        if type(vals)==dict:
            job_id=vals.get('job_id')
            job=job_id and self.env['edi.file.process.job'].browse(job_id) or False
        return super(tpw_transaction_log,self).create(vals)