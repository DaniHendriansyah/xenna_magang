{
    'name': 'Equipment Loan Tracker',
    'version': '1.0',
    'category': 'Operations',
    'summary': 'Modul untuk mencatat peminjaman alat kantor/lab',
    'description': """
        Custom module untuk melacak ketersediaan dan peminjaman alat.
        Fitur:
        - Pencatatan master data alat
        - Transaksi peminjaman dan pengembalian
        - Pelacakan status keterlambatan
    """,
    'author': 'Dani Hendriansyah',
    'website': '',
    'depends': ['base'],
    'data': [
        'views/menu.xml',  
        'views/equipment_item_views.xml',
        'views/equipment_loan_views.xml',
        'security/ir.model.access.csv',
        'reports/loan_report.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}