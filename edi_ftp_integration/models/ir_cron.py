from odoo import models,fields,api

class IrCron(models.Model):
    
    _inherit = "ir.cron"
    
    edi_group_id = fields.Many2one('edi.cron.group.ept',string="EDI Group ID")
    
    
    @api.model
    def create(self,vals):
        res = super(IrCron,self).create(vals)
        model = self.env.ref('edi_ftp_integration.model_edi_cron_group_ept')
        if res.edi_group_id and res.state == 'code' and res.model_id.id == model.id:
            res.with_context({'direct_write':True}).write({'code':"model.perform_cron_execution(group_ids=[%s])"%(res.edi_group_id.id)})
        return res
    
    @api.multi
    def write(self,vals):
        if self._context.get('direct_write',False):
            return super(IrCron,self).write(vals)
        res = super(IrCron,self).write(vals)
        model = self.env.ref('edi_ftp_integration.model_edi_cron_group_ept')
        for record in self:
            if record.edi_group_id and record.state == 'code' and record.model_id.id == model.id:
                record.with_context({'direct_write':True}).write({'code':"model.perform_cron_execution(group_ids=[%s])"%(record.edi_group_id.id)})
        return res
    
    @api.model
    def default_get(self, fields):
        res = super(IrCron, self).default_get(fields)
        if self._context.get('edi_group'):
            res['model_id'] = self.env.ref('edi_ftp_integration.model_edi_cron_group_ept').id
        return res