# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class ArcsActivity(models.Model):
    """A specific funded activity / work-plan line (e.g. a CIDA-funded
    consultancy, workshop, or translation line item). Mirrors the 'PIP
    Activity codes' dimension from the legacy NAV system.

    Paired 1-to-1 with an account.analytic.account on the dedicated
    'ARCS Activity' analytic plan, exactly like Branch/Donor/Project/
    Employee. Optional on every document -- most transactions won't
    need an Activity, only those tracked against a specific funded
    work-plan line will.

    Unlike Branch and Project, the source spreadsheet for this
    dimension is flat (no Totaling/grouping rows, no hierarchy), so
    there is no parent/child structure here. The optional `project_id`
    link lets the Activity list be filtered down once a Project is
    selected on a document, but it is not populated automatically on
    import -- the source data gives no reliable way to infer which
    Project each Activity code belongs to, so it is left blank for
    someone with domain knowledge to fill in afterwards.
    """
    _name = 'arcs.finance.activity'
    _description = 'ARCS Activity (Funded Work-Plan Line)'
    _order = 'complete_name'
    _rec_names_search = ['code', 'name']

    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account',
        required=True, ondelete='restrict', copy=False)
    code = fields.Char(related='analytic_account_id.code', store=True, readonly=False)
    name = fields.Char(related='analytic_account_id.name', store=True, readonly=False)
    complete_name = fields.Char(compute='_compute_complete_name', store=True)
    project_id = fields.Many2one(
        'arcs.finance.project', string='Project', ondelete='restrict',
        help="Optional: the Project this Activity belongs to. When set, this "
             "Activity will only appear on documents whose Project field "
             "matches, so codes stay easy to find.")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('analytic_account_uniq', 'unique(analytic_account_id)',
         'Each analytic account can only be linked to one ARCS activity.'),
    ]

    @api.depends('name', 'code')
    def _compute_complete_name(self):
        for activity in self:
            activity.complete_name = f"[{activity.code}] {activity.name}" if activity.code else activity.name

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for activity in self:
            activity.display_name = f"[{activity.code}] {activity.name}" if activity.code else (activity.name or '')

    @api.model_create_multi
    def create(self, vals_list):
        plan = self.env.ref('arcs_finance_data.analytic_plan_activity')
        for vals in vals_list:
            if not vals.get('analytic_account_id'):
                aa = self.env['account.analytic.account'].create({
                    'name': vals.get('name') or _('New Activity'),
                    'code': vals.get('code'),
                    'plan_id': plan.id,
                })
                vals['analytic_account_id'] = aa.id
        return super().create(vals_list)
