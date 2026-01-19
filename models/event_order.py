# -*- coding: utf-8 -*-

from odoo import models, fields


class EventOrder(models.Model):
    _name = "nextevent.order"
    _description = "Ordre d'Événement"

    name = fields.Char(
        string="Nom de l'événement",
        required=True,
    )

    description = fields.Text(
        string="Description",
    )

    attendees = fields.Integer(
        string="Nombre de participants",
        default=0,
    )

    event_type = fields.Char(
        string="Type d'événement (IA)",
        readonly=True,
    )

    estimated_duration = fields.Float(
        string="Durée estimée (h)",
        readonly=True,
    )

    estimated_budget = fields.Float(
        string="Budget estimé",
        readonly=True,
    )

    required_staff = fields.Integer(
        string="Personnel requis",
        readonly=True,
    )
