# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    # App information
   
    'name': 'Display Vendors Stock Info at your Online Store',
    'version': '11.0',
    'category': 'Website',
    'summary': """This App allows you to display vendors stock + product foretasted Stock Info at your Online Store""",
    
    # Dependencies
    
    'depends': ['website_sale_stock','dropship_edi_integration_ept'],
    
    # Views
    
    'data': [
        'views/website_templates.xml',
    ],
       
    # Odoo Store Specific
    
    'images': ['static/description/website_stock.png'],
       
    
    # Author

    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',
       
       
    # Technical 
    
    'installable': True,
    'currency': 'EUR',
    'auto_install': False,
    'application': True,
}