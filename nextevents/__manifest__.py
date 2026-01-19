# -*- coding: utf-8 -*-
{
    "name": "NextEvents",
    "version": "1.0.0",
    "summary": "Gestion intelligente des événements avec IA",
    "category": "Services/Events",
    "author": "Projet ENSA",
    "license": "LGPL-3",

    "depends": [
        "base",
        "mail",
    ],

    "data": [
        "security/ir.model.access.csv",
        "data/event_sequence.xml",
        "views/event_order_views.xml",
        "views/event_menu.xml",
    ],

    "application": True,
    "installable": True,
}
