{
  
   # App information
    
    'name': "Dropshipper EDI Integration in Odoo",
    'category': 'Purchases',
    'version': '11.0',
    'summary' : 'Odoo Dropshipper EDI Integration helps dropshipper to manage orders, products & inventory via EDI Integration through FTP Server.',
    'license': 'OPL-1',

   # Author
    
    "author": "Emipro Technologies Pvt. Ltd.",
    'website': 'http://www.emiprotechnologies.com/',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',
    
   # Dependencies
   
    'depends': ['sale', 'stock','delivery','auto_invoice_workflow_ept'],
    
   # View
    
    'data': [
        'view/edi_operation_wizard_view.xml',
        'view/ftp_server_view.xml',
        'view/product_product.xml',
        'view/edi_configuration.xml',
        'view/file_process_job.xml',
        'view/partner_product.xml',
        'view/map_product_wizard_view.xml',
        'view/res_partner.xml',
        'data/edi_configuration.xml',
        'data/edi_default_cron_group.xml',
        'view/edi_cron_group.xml',
        'security/ir.model.access.csv',
        'view/sale_order_view.xml',
    ],
    
    
    # Technical
    
    'images': ['static/description/Odoo-Dropshipper-Solution-Cover.jpg'],    
    'live_test_url':'http://www.emiprotechnologies.com/free-trial?app=edi-ftp-integration&version=11',
    'installable': True,
    'auto_install': False,
    'application' : True,
    'price': 249.00,
    'currency': 'EUR',
	
}
                                                                                                     
