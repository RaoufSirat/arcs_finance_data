# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class ArcsFinanceProgram(models.Model):
    """A programme (Disaster Management, Health Program, Marastoon Program, ...).
    Mirrors the programme-level rows of the legacy NAV "Project Codes" dimension.

    v2.0: split out of the old combined 'arcs.project' model (which held both
    Programs and Projects in one table, distinguished only by an is_program
    flag) into its own model, entirely separate from Projects. Also, as of
    v2.0, this name no longer collides with the unrelated 'arcs.project'
    model belonging to the arcs_grant module -- the two had been accidentally
    sharing one table/model name. See migrations/17.0.2.0.0/pre-migrate.py
    for how existing data was carried across with the same record ids.

    Paired 1-to-1 with an account.analytic.account on the 'ARCS Project'
    analytic plan (Programs and Projects share that one analytic plan, same
    as before the split).
    """
    _name = 'arcs.finance.program'
    _description = 'ARCS Programme'
    _order = 'name'
    _rec_names_search = ['code', 'name']

    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account',
        required=True, ondelete='restrict', copy=False)
    code = fields.Char(related='analytic_account_id.code', store=True, readonly=False)
    name = fields.Char(related='analytic_account_id.name', store=True, readonly=False)
    active = fields.Boolean(default=True)
    project_ids = fields.One2many(
        'arcs.finance.project', 'program_id', string='Projects in this Programme')

    _sql_constraints = [
        ('analytic_account_uniq', 'unique(analytic_account_id)',
         'Each analytic account can only be linked to one ARCS programme.'),
    ]

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for program in self:
            program.display_name = f"[{program.code}] {program.name}" if program.code else (program.name or '')

    @api.model_create_multi
    def create(self, vals_list):
        plan = self.env.ref('arcs_finance_data.analytic_plan_project')
        for vals in vals_list:
            if not vals.get('analytic_account_id'):
                aa = self.env['account.analytic.account'].create({
                    'name': vals.get('name') or _('New Programme'),
                    'code': vals.get('code'),
                    'plan_id': plan.id,
                })
                vals['analytic_account_id'] = aa.id
        return super().create(vals_list)
