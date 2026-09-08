{
    'name': "Perustakaan Management",
    'summary': "Perpustakaan Management Module",
    'description': """ This School Management Module is useful for Maintained the Student,Classes,School Transport and Hostel and More features of School""",
    'author': 'Xenna',
    'company': 'Xenna Technology',
    'maintainer': 'Xenna Technology',
    'website': "https://xennatech.com/",
    "license": "AGPL-3",
    'category': 'Education',
    'version': '18.0.1.0.0',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/data_buku.xml',
        'views/data_siswa.xml',
        'views/pinjam_buku.xml', 
        'views/dashboard.xml'
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
