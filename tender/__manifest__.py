{
    'name': 'Tender',
    'version': '1.0',
    'category': 'Project',
    'summary': 'Tender Management System',
    'description': """
        This module provides a comprehensive system for managing tenders, including creation, tracking, and reporting.
    """,
    'author': 'WELLSWORTH',
    'depends': ['base', 'mail', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'views/contract_views.xml',
        'views/tender_views.xml',
        'views/templates.xml',
        'views/tender_menus.xml',
        'data/tender_mail_template.xml',
    ],
    'installable': True,
    'application': True,
}