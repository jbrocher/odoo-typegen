from odoo import fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    x_followup_days = fields.Integer()

    def action_schedule_followup(self, days: int) -> bool:
        return True
