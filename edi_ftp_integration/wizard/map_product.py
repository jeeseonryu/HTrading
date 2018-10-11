from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
import base64
import csv

class map_product_wizard(models.TransientModel):
    
    _name = "map.product.wizard"
    
    partner_id = fields.Many2one('res.partner', string="Partner",domain=[('customer','=',True)])
    file = fields.Binary("Select File",filters='*.csv',help="Select File To Map Product.")
    file_delimiter=fields.Selection([('semicolon',';'),
                              ('colon',':'),
                              ('comma',','),
                              ('tab','{tab}')
                              ],
                             string="Delimiter",default='comma', help="Select a delimiter to process CSV file.")
    
    
    @api.one
    def validate_file_fields(self, fieldname):
        require_fields_import = ['Odoo SKU','Partner Product SKU']
        if len(fieldname) > len(require_fields_import):
            raise ValidationError(_('Incorrect file format found..! File Contains Extra fields'))
        if len(fieldname) < len(require_fields_import):
            raise ValidationError(_('Incorrect file format found..! Please provide all the required fields in file'))
        return True
    
    @api.multi
    def map_product_file_process(self):
    
        csv_file = base64.decodestring(self.file)
        partner_product_obj = self.env['partner.product.ept']
        product_product_obj = self.env['product.product']
        file_write = open('/tmp/map_product.csv',"wb")
        file_write.write(csv_file)
        delimiter_data={'semicolon':';','colon':':','comma':',','tab':'\t'}
        file_write.close()
        file_delimiter = delimiter_data.get(str(self.file_delimiter))
        lines = csv.reader(open('/tmp/map_product.csv',"rt", encoding="utf-8"),delimiter=file_delimiter, quotechar='"')
        flag = True
        for line in lines:
            if flag:
                self.validate_file_fields(line)
                flag=False
                continue
            if (not line[1]) or (not line[0]):
                continue
            partner_product_id = partner_product_obj.search([('partner_id','=',self.partner_id.id),('product_id.default_code','=',line[0])],limit=1)
            if partner_product_id:
                partner_product_id.write({'sku':line[1]})
                continue
            else:
                product_id = product_product_obj.search([('default_code','=',line[0])],limit=1)
                if not product_id:
                    continue 
                product_vals = {
                                'partner_id':self.partner_id and self.partner_id.id,
                                'product_id':product_id and product_id.id,
                                'sku':line[1]
                                }
                partner_product_obj.create(product_vals)
        return True
