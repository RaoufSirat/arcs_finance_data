# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class ArcsFinanceProject(models.Model):
    """A project under a Programme, or a standalone department/office code.
    Mirrors the project-level rows of the legacy NAV "Project Codes" dimension.

    v2.0: split out of the old combined 'arcs.project' model into its own
    model, separate from Programs -- 'program_id' below replaces what used
    to be a self-referential 'parent_id' on the combined model. Also, as of
    v2.0, the name 'arcs.project' itself is no longer used by this module at
    all, so it no longer collides with the unrelated 'arcs.project' model
    belonging to the arcs_grant module. See
    migrations/17.0.2.0.0/pre-migrate.py for how existing data was carried
    across with the same record ids.

    Paired 1-to-1 with an account.analytic.account on the 'ARCS Project'
    analytic plan. Optional on both revenue and expense lines -- unlike
    Branch, not every transaction relates to a specific project (NAV itself
    ships an explicit "Non project Dimension" code for that case, which is
    intentionally not imported here -- simply leave the Project field blank).
    """
    _name = 'arcs.finance.project'
    _description = 'ARCS Project'
    _order = 'complete_name'
    _rec_names_search = ['code', 'name']

    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account',
        required=True, ondelete='restrict', copy=False)
    code = fields.Char(related='analytic_account_id.code', store=True, readonly=False)
    name = fields.Char(related='analytic_account_id.name', store=True, readonly=False)
    complete_name = fields.Char(compute='_compute_complete_name', store=True)
    program_id = fields.Many2one(
        'arcs.finance.program', string='Programme', ondelete='restrict',
        help="The programme this project belongs to, if any.")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('analytic_account_uniq', 'unique(analytic_account_id)',
         'Each analytic account can only be linked to one ARCS project.'),
    ]

    @api.depends('name', 'program_id.name')
    def _compute_complete_name(self):
        for project in self:
            if project.program_id:
                project.complete_name = f"{project.program_id.name} / {project.name}"
            else:
                project.complete_name = project.name

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for project in self:
            project.display_name = f"[{project.code}] {project.name}" if project.code else (project.name or '')

    @api.model_create_multi
    def create(self, vals_list):
        plan = self.env.ref('arcs_finance_data.analytic_plan_project')
        for vals in vals_list:
            if not vals.get('analytic_account_id'):
                aa = self.env['account.analytic.account'].create({
                    'name': vals.get('name') or _('New Project'),
                    'code': vals.get('code'),
                    'plan_id': plan.id,
                })
                vals['analytic_account_id'] = aa.id
        return super().create(vals_list)
