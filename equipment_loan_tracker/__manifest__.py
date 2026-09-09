{
    'name': 'Equipment Loan Tracker',
    'version': '1.0.0',
    'category': 'Operations',
    'summary': 'Equipment loan management integrated with Inventory, Invoicing, and Portal',
    'description': """
Equipment Loan Tracker
======================

Sistem peminjaman barang yang terintegrasi dengan:
- Product
- Inventory
- Invoicing / Accounting
- Portal Self-Service
    """,
    'author': 'Xennatech',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'product',
        'stock',
        'account',
        'portal',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/portal_security.xml',
        'views/loan_report.xml',
        'views/equipment_loan_views.xml',
        'views/product_template_views.xml',
        'views/portal_templates.xml',
        'data/locations.xml',
        'data/stock_data.xml',
        'data/email_data.xml',
    ],
    'installable': True,
    'application': True,
}