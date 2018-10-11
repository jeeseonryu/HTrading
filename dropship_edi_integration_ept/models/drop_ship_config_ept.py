from odoo import models,fields,api

class ftp_server_ept(models.Model):
    
    _name="drop.ship.server.ept"
    
    name=fields.Char("Server name",help ='Name of FTP Host')
    host=fields.Char("Host",help ='Supplier FTP Host Address')
    username=fields.Char("User Name",copy=False,help ='Your Username')
    password=fields.Char("Password",copy=False,help ='Your Username Password ')
    port=fields.Char("Port")
    directory_ids=fields.One2many("directory.ept",'server_id',string="Directory list")

    _sql_constraints = [
        ('ftp_unique_ept', 'UNIQUE (name,host,username,password,port)',
         'The Server must be unique!'),
    ]

class directory_ept(models.Model):
    
    _name="directory.ept"

    server_id=fields.Many2one("drop.ship.server.ept",string="Ftp Server")
    name=fields.Char("Name")
    path=fields.Char("Path")

    _sql_constraints = [
        ('directory_unique', 'UNIQUE (name,server_id)',
         'The Directory must be unique!'),]
    
    