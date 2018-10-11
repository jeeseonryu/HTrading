from odoo import models,fields,api

class _transaction_log(models.Model):

    _name = 'dropship.transaction.log.ept'
    _rec_name='job_id'
    _order='id desc'
    
    job_id = fields.Many2one('dropship.file.process.job.ept',string="Job")
    tracking_no = fields.Char(string="Tracking No")
    message = fields.Text(string="Message")