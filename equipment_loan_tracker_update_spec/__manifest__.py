{
    'name': 'Equipment Loan Tracker Update Spec',
    'version': '1.0.0',
    'category': 'Operations',
    'summary': 'Equipment loan management integrated with Inventory and Invoicing',
    'description': """
Equipment Loan Tracker
======================

Sistem peminjaman barang yang terintegrasi dengan:
- Product
- Inventory
- Invoicing / Accounting
    """,

    'author': 'Xennatech',
    'license': 'LGPL-3',

    'depends': [
        'base',
        'product',
        'stock',
        'account',
    ],

'data': [
    'security/ir.model.access.csv',
    'views/loan_report.xml',
    'views/equipment_loan_views.xml',
    'views/product_template_views.xml',
    'data/locations.xml',
    'data/stock_data.xml',
],

    'installable': True,
    'application': True,
}