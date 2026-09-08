from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    loan_penalty_amount = fields.Monetary(
        string='Denda Kehilangan',
        currency_field='currency_id',
        help='Nominal denda jika produk dinyatakan hilang.'
    )

    penalty_fee = fields.Float(string='Biaya Denda Hilang', default=0.0)