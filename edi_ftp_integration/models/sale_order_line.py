from odoo import models,fields,api

class SaleOrderLine(models.Model):
    
    _inherit="sale.order.line"

    def create_sale_order_line_dict(self,partner,product,qty,price,sale_order):
        amount_per_unit = 0.0
        pricelist = sale_order.pricelist_id or partner.property_product_pricelist
        if not price:
            amount_per_unit = pricelist.price_get(product.id,qty)[pricelist.id] or 0.0
        else:
            amount_per_unit = price

        ordervals={
                   'order_id':sale_order.id,
                   'product_id':product.id,
                   'product_uom_qty':qty,
                   'price_unit':amount_per_unit,
                   'product_uom':product.uom_id.id,        
                  }

        new_record=self.new(ordervals)
        
        new_record.product_id_change()
        new_record.product_uom_qty=qty
        #new_record.product_uom_change()
        new_record._onchange_discount()
        
        if price:
            new_record.price_unit=amount_per_unit

        order_line_vals=new_record._convert_to_write(new_record._cache)
        
        return order_line_vals
