from odoo import models, fields, api,_
import base64
import requests
from datetime import datetime

class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    main_product_id = fields.Char(string="Main Product ID", readonly=True)
    
    @api.multi
    def create_or_update_products(self, product_ids=False, partner_ids=False, is_cron=False):
        product_attribute_obj = self.env['product.attribute']
        product_attribute_value_obj = self.env['product.attribute.value']
        product_attribute_line_obj = self.env['product.attribute.line']
        dropship_product_obj = self.env['dropship.product.ept']
        product_obj = self.env['product.product']
        transaction_log_obj = self.env['dropship.transaction.log.ept']
        stock_location_route_obj = self.env['stock.location.route']
        for partner_id in partner_ids:
            date_time = datetime.now()
            job_filename = "%s_%s" % (partner_id.name, date_time.strftime('%Y%m%d%H%M%S.csv'))
            job = self.env['dropship.file.process.job.ept'].create({
                                                                    'application':'product',
                                                                    'operation_type':'create',
                                                                    'partner_id':partner_id.id,
                                                                    'is_processed':True,
                                                                    'filename':job_filename
                                                                    })
            dropship_product_ids = dropship_product_obj.search([('partner_id', '=', partner_id.id),('id', 'in', product_ids.ids)])
            for dropship_product_id in dropship_product_ids:
                total_product_updated = 0
                total_product_created = 0
                for line_id in dropship_product_id.dropship_product_line:
                    route_id = stock_location_route_obj.search([('is_dropshipping','=',True)])
                    date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    main_product_id = self.search([('main_product_id', '=', dropship_product_id.main_product_id)])
                    barcode_product_id = product_obj.search([('barcode','=',line_id.barcode)],limit=1)
                    if barcode_product_id:
                        transaction_log_obj.create({'job_id':job.id
                                                    ,'message' : """Barcode %s Skipped due to duplication. Product - %s"""%(line_id.barcode,line_id.name)
                                                    })
                        line_id.barcode = False
                    if not main_product_id:
                        product_id = False
                        image_url = line_id.image_url
                        category = line_id.category
                        if image_url :
                            filename = requests.get(image_url)
                            image_url = base64.b64encode(filename.content)
                        
                        categ_id = self.env['product.category'].search([('name', '=', category)], limit=1)
                        if is_cron and partner_id.auto_create_category:
                            if not categ_id:
                                categ_id = self.env['product.category'].create({'name':category})
                        elif is_cron and not partner_id.auto_create_category:
                            if not categ_id:
                                transaction_log_obj.create({'job_id':job.id
                                                            ,'message' : """Product %s Skipped Due to Category not found in Odoo. ||File - %s"""% (line_id.name, dropship_product_id.filename)
                                                            })
                                continue
                        else:    
                            if not categ_id :
                                categ_id = self.env['product.category'].create({'name':category})
                        if line_id.default_code:
                            product_id = product_obj.create({
                                                            'name':dropship_product_id.name,
                                                            'weight':line_id.weight or 0.0,
                                                            'type':'product',
                                                            'description_sale':line_id.description or False,
                                                            'barcode':line_id.barcode or False,
                                                            'default_code':line_id.default_code or False,
                                                            'categ_id':categ_id.id or False,
                                                            'image_medium':image_url or False,
                                                            'tags':line_id.tags or False,
                                                            'route_ids':[(6,0,route_id.ids)],
                                                            })
                            vendor_code_id = self.env['product.supplierinfo'].create({'product_id':product_id.id, 'name':dropship_product_id.partner_id.id,'product_tmpl_id':product_id.product_tmpl_id.id,'price':line_id.price or 0.0})
                            transaction_log_obj.create({'job_id':job.id
                                                        ,'message' : """Product %s Created In Odoo. Product - %s. File - %s"""% (line_id.default_code,product_id.name,dropship_product_id.filename)
                                                        })
                            total_product_created = total_product_created + 1
                            product_tmpl_id = product_id.product_tmpl_id
                            product_tmpl_id.write({'type':'product',
                                                   'main_product_id':dropship_product_id.main_product_id,
                                                })
                            dropship_product_id.write({'is_processed':True})
                            
                        elif line_id.vendor_code:
                            vendor_code_id = self.env['product.supplierinfo'].search([('product_code', '=', line_id.vendor_code),('name', '=', dropship_product_id.partner_id.id)],limit=1)
                            product_id = product_obj.create({
                                                            'name':dropship_product_id.name,
                                                            'weight':line_id.weight or 0.0,
                                                            'type':'product',
                                                            'description_sale':line_id.description or False,
                                                            'barcode':line_id.barcode or 0.0,
                                                            'categ_id':categ_id.id or False,
                                                            'image_medium':image_url or False,
                                                            'tags':line_id.tags or False,
                                                            'route_ids':[(6,0,route_id.ids)],
                                                            })
                            transaction_log_obj.create({'job_id':job.id,
                                                        'message' : """Product %s Created In Odoo. Product - %s. File - %s"""% (line_id.vendor_code,product_id.name,dropship_product_id.filename)
                                                        })
                            total_product_created = total_product_created + 1
                            if vendor_code_id:
                                vendor_code_id = vendor_code_id.write({'product_id':product_id.id, 'product_tmpl_id':product_id.product_tmpl_id.id})
                            else :
                                vendor_code_id = self.env['product.supplierinfo'].create({'product_id':product_id.id, 'name':dropship_product_id.partner_id.id, 'product_code':line_id.vendor_code,'product_tmpl_id':product_id.product_tmpl_id.id,'price':line_id.price or 0.0})                                
                                
                        product_tmpl_id = product_id.product_tmpl_id
                        product_tmpl_id.write({'type':'product',
                                               'main_product_id':dropship_product_id.main_product_id,
                                               })
                        dropship_product_id.write({'is_processed':True})
                        
                        if product_id and line_id.attribute_name and line_id.attribute_value :
                            for attr_name, attr_value in zip(line_id.attribute_name.split(','), line_id.attribute_value.split(',')):
                                attribute_id = product_attribute_obj.search([('name', '=', attr_name)], limit=1)
                                if not attribute_id:
                                    attribute_id = product_attribute_obj.create({'name':attr_name})
                                attrib_value_id = product_attribute_value_obj.search([('attribute_id', '=', attribute_id.id), ('name', '=', attr_value)], limit=1)
                                if not attrib_value_id:
                                    attrib_value_id = product_attribute_value_obj.create({'attribute_id':attribute_id.id, 'name':attr_value})
                                product_attribute_line_id = product_attribute_line_obj.search([('product_tmpl_id', '=', product_tmpl_id.id), ('attribute_id', '=', attribute_id.id)])
                                if product_attribute_line_id:
                                    product_attribute_id = product_attribute_line_obj.search([('product_tmpl_id', '=', product_tmpl_id.id), ('attribute_id', '=', attribute_id.id), ('value_ids', 'in', attrib_value_id.ids)], limit=1)
                                    if not product_attribute_id:
                                        value_ids = product_attribute_line_id.value_ids.ids or []
                                        value_ids += attrib_value_id.ids
                                        product_attribute_line_id.write({'value_ids':[(6, 0, list(set(value_ids)))]})
                                if not product_attribute_line_id:
                                    product_attribute_line_id = product_attribute_line_obj.create({'product_tmpl_id':product_tmpl_id.id, 'attribute_id':attribute_id.id, 'value_ids':[(6, 0, attrib_value_id.ids)]})
                                product_id.write({'attribute_value_ids':[(4,attrib_value_id.id)]}) 
                    else:
                        product_id = False
                        image_url = line_id.image_url or False
                        category = line_id.category
                        if image_url :
                            filename = requests.get(image_url)
                            image_url = base64.b64encode(filename.content)
                        
                        categ_id = self.env['product.category'].search([('name', '=', category)], limit=1)
                        if is_cron and partner_id.auto_create_category:
                            if not categ_id:
                                categ_id = self.env['product.category'].create({'name':category})
                        elif is_cron and not partner_id.auto_create_category:
                            if not categ_id:
                                transaction_log_obj.create({'job_id':job.id,
                                                            'message' : """Product %s Skipped Due to Category %s not found in Odoo. File - %s"""% (line_id.name,category,dropship_product_id.filename)
                                                            })
                                continue
                        else:    
                            if not categ_id :
                                categ_id = self.env['product.category'].create({'name':category})
                        if line_id.default_code:
                            product_id = product_obj.search([('default_code', '=', line_id.default_code)])
                            if not product_id:
                                product_id = product_obj.create({
                                                                'product_tmpl_id':product_tmpl_id.id,
                                                                'name':dropship_product_id.name,
                                                                'weight':line_id.weight or 0.0,
                                                                'type':'product',
                                                                'description_sale':line_id.description or False,
                                                                'barcode':line_id.barcode or False,
                                                                'default_code':line_id.default_code or False,
                                                                'categ_id':categ_id.id or False,
                                                                'image_medium':image_url or False,
                                                                'tags':line_id.tags or False,
                                                                'route_ids':[(6,0,route_id.ids)],
                                                                })
                                vendor_code_id = self.env['product.supplierinfo'].create({'product_id':product_id.id,'name':dropship_product_id.partner_id.id,'product_tmpl_id':product_id.product_tmpl_id.id,'price':line_id.price or 0.0})
                                transaction_log_obj.create({'job_id':job.id,
                                                            'message' : """Product %s Created In Odoo. Product - %s File - %s"""%(line_id.default_code,product_id.name,dropship_product_id.filename)
                                                            })
                                total_product_created = total_product_created + 1
                            else:
                                vendor_code_id = self.env['product.supplierinfo'].search([('name','=',dropship_product_id.partner_id.id),('product_id','=',product_id.id)],limit=1)
                                product_id.write({
                                                'name':dropship_product_id.name,
                                                'weight':line_id.weight or 0.0,
                                                'description_sale':line_id.description or False,
                                                'barcode':line_id.barcode or False,
                                                'type':'product',
                                                'default_code':line_id.default_code or False,
                                                'categ_id':categ_id.id or False,
                                                'image_medium':image_url or False,
                                                'tags':line_id.tags or False,
                                                })
                                transaction_log_obj.create({'job_id':job.id
                                                            ,'message' : """Product %s Updated In Odoo. Product - %s. File - %s"""% (line_id.default_code,product_id.name,dropship_product_id.filename)
                                                            })
                                total_product_updated = total_product_updated + 1
                                if vendor_code_id:
                                    vendor_code_id = vendor_code_id.write({'product_id':product_id.id,'price':line_id.price or 0.0})
                                else :
                                    vendor_code_id = self.env['product.supplierinfo'].create({'product_id':product_id.id, 'name':dropship_product_id.partner_id.id,'price':line_id.price or 0.0})
                                    
                        elif line_id.vendor_code:
                            vendor_code_id = self.env['product.supplierinfo'].search([('product_code','=',line_id.vendor_code),('name','=', dropship_product_id.partner_id.id)],limit=1)
                            if not vendor_code_id and not vendor_code_id.product_id:
                                product_id = product_obj.create({
                                                                'product_tmpl_id':product_tmpl_id.id,
                                                                'name':dropship_product_id.name,
                                                                'weight':line_id.weight or 0.0,
                                                                'type':'product',
                                                                'description_sale':line_id.description or False,
                                                                'barcode':line_id.barcode or False,
                                                                'categ_id':categ_id.id or False,
                                                                'image_medium':image_url or False,
                                                                'tags':line_id.tags or False,
                                                                'route_ids':[(6,0,route_id.ids)],
                                                                })
                                transaction_log_obj.create({'job_id':job.id,
                                                            'message' : """Product %s Created In Odoo.Product - %s. ||File - %s"""% (line_id.vendor_code,product_id.name,dropship_product_id.filename)
                                                            })
                                total_product_created = total_product_created + 1
                                vendor_code_id = self.env['product.supplierinfo'].create({'product_id':product_id.id,'name':dropship_product_id.partner_id.id,'product_code':line_id.vendor_code,'product_tmpl_id':product_id.product_tmpl_id.id,'price':line_id.price or 0.0})
                            else:
                                product_id = vendor_code_id.product_id
                                product_id.write({
                                                'product_tmpl_id':product_id.product_tmpl_id.id,
                                                'name':dropship_product_id.name,
                                                'weight':line_id.weight or 0.0,
                                                'description_sale':line_id.description or False,
                                                'barcode':line_id.barcode or False,
                                                'type':'product',
                                                'categ_id':categ_id.id or False,
                                                'image_medium':image_url or False,
                                                'tags':line_id.tags or False,
                                                })
                                transaction_log_obj.create({'job_id':job.id
                                                            ,'message' : """Product %s Updated In Odoo. Product - %s. File - %s"""% (line_id.vendor_code,product_id.name,dropship_product_id.filename)
                                                            })
                                total_product_updated = total_product_updated + 1
                        product_tmpl_id = product_id.product_tmpl_id
                        product_tmpl_id.write({'type':'product',
                                               'main_product_id':dropship_product_id.main_product_id,
                                               'name':dropship_product_id.name,
                                               })
                        if product_id and line_id.attribute_name and line_id.attribute_value :
                            for attr_name, attr_value in zip(line_id.attribute_name.split(','), line_id.attribute_value.split(',')):
                                attribute_id = product_attribute_obj.search([('name', '=', attr_name)], limit=1)
                                if not attribute_id:
                                    attribute_id = product_attribute_obj.create({'name':attr_name})
                                attrib_value_id = product_attribute_value_obj.search([('attribute_id', '=', attribute_id.id), ('name', '=', attr_value)], limit=1)
                                if not attrib_value_id:
                                    attrib_value_id = product_attribute_value_obj.create({'attribute_id':attribute_id.id, 'name':attr_value})
                                product_attribute_line_id = product_attribute_line_obj.search([('product_tmpl_id', '=', product_tmpl_id.id), ('attribute_id', '=', attribute_id.id)])
                                if product_attribute_line_id:
                                    product_attribute_id = product_attribute_line_obj.search([('product_tmpl_id', '=', product_tmpl_id.id), ('attribute_id', '=', attribute_id.id), ('value_ids', 'in', attrib_value_id.ids)], limit=1)
                                    if not product_attribute_id:
                                        value_ids = product_attribute_line_id.value_ids.ids or []
                                        value_ids += attrib_value_id.ids
                                        product_attribute_line_id.write({'value_ids':[(6, 0, list(set(value_ids)))]})
                                if not product_attribute_line_id:
                                    product_attribute_line_id = product_attribute_line_obj.create({'product_tmpl_id':product_tmpl_id.id, 'attribute_id':attribute_id.id, 'value_ids':[(6, 0, attrib_value_id.ids)]})
                                product_id.write({'attribute_value_ids':[(4,attrib_value_id.id)]})
                
                transaction_log_obj.create({'job_id':job.id,
                                            'message' : """Products %s Created/Updated In Odoo.
                                            ||Total Updated %s
                                            ||Total Created %s"""% (dropship_product_id.name,total_product_updated, total_product_created)
                                            })
        return True
    
    @api.multi
    def auto_create_or_update_products(self,ctx={}):
        partner_obj = self.env['res.partner']
        dropship_product_ept_obj = self.env['dropship.product.ept']
        if not isinstance(ctx,dict) or not 'partner_id' in ctx:
            return True
        partner_id = ctx.get('partner_id',False)
        partner_ids = partner_obj.browse(partner_id)
        
        product_ids = dropship_product_ept_obj.search([('partner_id', 'in', partner_ids.ids)])
        
        if product_ids and partner_ids:
            self.create_or_update_products(product_ids, partner_ids, is_cron=True)
        return True
        
