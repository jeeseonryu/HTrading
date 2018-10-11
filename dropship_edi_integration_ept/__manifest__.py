{
  
   # App information
   
    'name': "Dropshipping EDI Integration in Odoo",
    'category': 'Purchases',
    'version': '11.0',
    'summary' : 'Dropshipping EDI Integration in Odoo helps the seller to manage products, orders & inventory via EDI Integration through the FTP Server.',
    'license': 'OPL-1',

   # Author
    
    "author": "Emipro Technologies Pvt. Ltd.",
    'website': 'http://www.emiprotechnologies.com/',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',
    
   # Dependencies
   
    'depends': ['sale', 'stock','delivery','purchase','website_sale','stock_dropshipping'],
    
   # View
    
    'data': ['view/drop_ship_config_ept_view.xml',
             'view/file_process_job_ept_view.xml',
             'wizard/dropship_operations_view.xml',
             'view/res_partner.xml',
             'view/dropship_product_ept_view.xml',
             'view/active_suppliers_ept.xml',
             'view/product_template.xml',
             'data/ir_cron.xml',
             'view/dropship_product_line_ept_view.xml',
             'view/product_supplierinfo_ept.xml',
             'view/stock_picking_type_view.xml',
             'view/stock_picking_view.xml',
             'security/ir.model.access.csv',
             'view/product_product.xml',
             'data/stock_data.xml',
             ],
    
    
    
    'images': ['static/description/Dropshipper-EDI-Integration-in-Odoo-COver.jpg'],    
    'live_test_url':'https://www.emiprotechnologies.com/free-trial?app=dropship-edi-integration-ept&version=11&edition=enterprise',
    'installable': True,
    'auto_install': False,
    'application' : True,
    'price': '249',
    'currency': 'EUR',
}
