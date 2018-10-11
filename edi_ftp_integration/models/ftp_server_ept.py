from odoo import models,fields,api

class ftp_server_ept(models.Model):
    
    _name="ftp.server.ept"
    
    name=fields.Char("Server name",required=True)
    ftp_host=fields.Char("Host",required=True)
    ftp_username=fields.Char("User Name",required=True)
    ftp_password=fields.Char("Password",required=True)
    ftp_port=fields.Char("Port",required=True)
    is_passive_mode=fields.Boolean("Passive Mode",default=True)
    directory_ids=fields.One2many("ftp.directory.ept",'ftp_server_id',string="Directory list")

    _sql_constraints = [
        ('ftp_unique_ept', 'UNIQUE (name,ftp_host,ftp_username,ftp_password,ftp_port)',
         'The Server must be unique!'),
    ]

class ftp_directory_ept(models.Model):
    
    _name="ftp.directory.ept"

    ftp_server_id=fields.Many2one("ftp.server.ept",string="Ftp Server")
    name=fields.Char("Name",required=True)
    path=fields.Char("Path",required=True)
    partner_id = fields.Many2one('res.partner',"Partner")

    _sql_constraints = [
        ('directory_unique', 'UNIQUE (name,ftp_server_id)',
         'The Directory must be unique!'),
    ]
    