from odoo import models,fields,api

class dropship_file_process_job(models.Model):
    
    _name="dropship.file.process.job.ept"
    _description = "EDI Log"
    _inherit = ['mail.thread']
    _order='id desc'
    
    name = fields.Char("Name")
    filename = fields.Char("File Name")
    transaction_log_ids = fields.One2many("dropship.transaction.log.ept","job_id",string="Log")
    operation_type = fields.Selection([('import','Import'),('export','Export'),('create','Create')]
                                      ,string="Operation")
    application = fields.Selection([('sales','Sales')
                                    ,('shipment','Delivery')
                                    ,('invenotry','Stock')
                                    ,('product','Product')
                                    ,('other','Other')],string="Application")    
    message=fields.Text("Message")
    company_id=fields.Many2one('res.company',string="Company")
    partner_id = fields.Many2one('res.partner',string="Supplier")
    
            
    @api.model
    def create(self,vals):
        sequence=self.env.ref("dropship_edi_integration_ept.seq_dropship_file_process_job")
        name = sequence and sequence.next_by_id() or '/'
        company_id=self._context.get('company_id',self.env.user.company_id.id)
        if type(vals)==dict:
            vals.update({'name':name,'company_id':company_id})
        return super(dropship_file_process_job,self).create(vals)
            