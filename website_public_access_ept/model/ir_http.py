# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models
from odoo.http import request
import werkzeug.utils
from odoo import http
import logging

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _dispatch(cls):   
        url=request.httprequest.path
        
        #if not request.session['login'] and (url.find('/web/login')==-1 or url.find('_odoo/paas') ==-1):
        if not request.session['login'] and url.find('/web/login')==-1:
            if url.find('/web/')==-1 and url.find('/website/lang/')==-1  and url.find('/website/translations')==-1:
                _logger.info("\n****** website public access url:_displtch method of ir.http for url %s"%url)
                redirect = '/web/login'
                return http.redirect_with_hash(redirect)
        
        
        return super(IrHttp, cls)._dispatch()
