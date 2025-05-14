{
    'name': 'Estate',
    'version': '1.0',
    'depends': ['base', 'website'],
    'author': 'Ojo Ayanfe',
    'category': 'Real Estate',
    'summary': 'Manage real estate properties',
    'installable': True,
    'application': True,
    'data' : [
        'security/ir.model.access.csv',
        'views/estate_property_views.xml',
        'views/estate_menus.xml',
        'views/website_estate_templates.xml',
        'views/estate_property_offer_views.xml',
        'views/estate_property_type_views.xml',
        'views/estate_property_tag_views.xml',
        'views/res_users_views.xml',
    ]
}
