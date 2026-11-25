from odoo import _, api, fields, models


class ArcsBranch(models.Model):
    """ARCS organizational branch with a shared analytic account."""

    _name = 'arcs.finance.branch'

    _description = 'ARCS Branch / Collection Point'

    _order = 'complete_name'

    _rec_names_search = ['code', 'name']

    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account',
        required=True, ondelete='restrict', copy=False,
        help="The analytic account that carries this branch's revenue and expense postings.")

    code = fields.Char(related='analytic_account_id.code', store=True, readonly=False)

    name = fields.Char(related='analytic_account_id.name', store=True, readonly=False)

    complete_name = fields.Char(compute='_compute_complete_name', store=True)

    region_id = fields.Many2one(
        'arcs.finance.region', string='Region / Zone', ondelete='restrict', index=True,
        help="The Region this branch reports to. The two NAV codes with no zone prefix "
             "(HQS Headquarters, C-HSPT Central Hospital) are attached to the HQ record "
             "itself, so every branch rolls up somewhere.")

    region_type = fields.Selection(related='region_id.region_type', store=True)

    active = fields.Boolean(default=True)
    serial_no = fields.Char(string='Serial No.', index=True, copy=False)

    _sql_constraints = [
        ('analytic_account_uniq', 'unique(analytic_account_id)',
         'Each analytic account can only be linked to one ARCS branch.'),
    ]

    @api.depends('name', 'region_id.name')
    def _compute_complete_name(self):
        for branch in self:
            if branch.region_id:
                branch.complete_name = f"{branch.region_id.name} / {branch.name}"
            else:
                branch.complete_name = branch.name

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for branch in self:
            branch.display_name = (
                f"[{branch.code}] {branch.name}" if branch.code else (branch.name or ''))

    @api.model_create_multi
    def create(self, vals_list):
        plan = self.env.ref('arcs_finance_data.analytic_plan_branch')
        for vals in vals_list:
            if not vals.get('analytic_account_id'):
                account = self.env['account.analytic.account'].create({
                    'name': vals.get('name') or _('New Branch'),
                    'code': vals.get('code'),
                    'plan_id': plan.id,
                })
                vals['analytic_account_id'] = account.id
        return super().create(vals_list)
