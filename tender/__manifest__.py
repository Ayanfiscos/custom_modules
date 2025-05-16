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
        'data/report_action.xml',             # Only needed if extra report actions are defined here
        'views/tender_menus.xml',
        'views/extend_deadline_wizard.xml',
        'views/select_manager_wizard.xml',
    ],

    'installable': True,
    'application': True,
}