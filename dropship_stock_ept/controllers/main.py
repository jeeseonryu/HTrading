# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.http import request
from odoo.tools.pycompat import izip
from odoo.addons.website_sale_stock.controllers.main import WebsiteSale

class WebsiteSale(WebsiteSale):

    def get_attribute_value_ids(self, product):
        res = super(WebsiteSale, self).get_attribute_value_ids(product)
        variant_ids = [r[0] for r in res]
        for r, variant in izip(res, request.env['product.product'].sudo().browse(variant_ids)):
            for value in res:
                for r in value:
                    if type(r) is dict and value[0]==variant.id and 'virtual_available' in r.keys():
                        r.update({'virtual_available': variant.net_qty})
        return res