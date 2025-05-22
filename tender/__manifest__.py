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
        'reports/report_tender_document.xml',
        'data/email_templates.xml',
        'data/tender_mail_template.xml',
        'data/report_action.xml',
        'views/tender_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tender/static/src/js/tender_inspection_popup.js',
        ],
    },

    'installable': True,
    'application': True,
}