from odoo import models, fields, api, _
from odoo.osv.osv import except_osv
from odoo.exceptions import Warning
import pytz

class global_channel(models.Model):
    _inherit = "account.invoice"
    
    global_channel_id=fields.Many2one('global.channel.ept' ,string='Global Channel')
    
    @api.multi
    def action_move_create(self):
        result=super(global_channel,self).action_move_create()
        for record in self : 
            record.move_id.global_channel_id  = record.global_channel_id
            for line in record.move_id.line_ids:
                line.global_channel_id=record.global_channel_id.id
            
        return result