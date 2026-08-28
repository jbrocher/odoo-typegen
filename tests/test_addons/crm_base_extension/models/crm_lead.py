from odoo import fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    x_base_code = fields.Char()
    x_is_priority = fields.Boolean()

    def action_mark_priority(self) -> None:
        pass
