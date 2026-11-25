from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ArcsFinanceRegion(models.Model):
    """ARCS organizational region with a shared analytic account."""

    _name = 'arcs.finance.region'

    _description = 'ARCS Region / Zone'

    _order = 'complete_name'

    _parent_name = 'parent_id'

    _parent_store = True

    _rec_names_search = ['code', 'name']

    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account',
        required=True, ondelete='restrict', copy=False,
        help="The analytic account that carries this region's own postings -- money "
             "held or spent at region level, not yet attributed to one of its branches.")

    code = fields.Char(related='analytic_account_id.code', store=True, readonly=False)

    name = fields.Char(related='analytic_account_id.name', store=True, readonly=False)

    complete_name = fields.Char(compute='_compute_complete_name', store=True, recursive=True)

    region_type = fields.Selection([
        ('hq', 'Headquarters'),
        ('zone', 'Region / Zone'),
    ], required=True, default='zone', string='Level',
        help="Headquarters is the single top node of the ARCS structure. Every other "
             "record here is a Region / Zone office sitting under it.")

    parent_id = fields.Many2one(
        'arcs.finance.region', string='Reports To', ondelete='restrict',
        help="The region this one reports to -- normally Headquarters.")

    parent_path = fields.Char(index=True, unaccent=False)

    child_ids = fields.One2many('arcs.finance.region', 'parent_id', string='Sub-Regions')

    branch_ids = fields.One2many(
        'arcs.finance.branch', 'region_id', string='Branches in this Region')

    branch_count = fields.Integer(compute='_compute_branch_count')
    child_region_count = fields.Integer(compute='_compute_child_region_count')

    active = fields.Boolean(default=True)
    serial_no = fields.Char(string='Serial No.', index=True, copy=False)

    _sql_constraints = [
        ('analytic_account_uniq', 'unique(analytic_account_id)',
         'Each analytic account can only be linked to one ARCS region.'),
    ]

    @api.constrains('parent_id')
    def _check_region_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('A region cannot be placed under itself.'))

    @api.depends('name', 'parent_id.complete_name', 'region_type')
    def _compute_complete_name(self):
        for region in self:
            if region.parent_id and region.region_type != 'hq':
                region.complete_name = f"{region.parent_id.name} / {region.name}"
            else:
                region.complete_name = region.name

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for region in self:
            region.display_name = (
                f"[{region.code}] {region.name}" if region.code else (region.name or ''))

    def action_view_branches(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Branches: %s', self.display_name),
            'res_model': 'arcs.finance.branch',
            'view_mode': 'tree,form',
            'domain': [('region_id', '=', self.id)],
            'context': {'default_region_id': self.id},
        }

    @api.model_create_multi
    def create(self, vals_list):
        plan = self.env.ref('arcs_finance_data.analytic_plan_region')
        for vals in vals_list:
            if not vals.get('analytic_account_id'):
                account = self.env['account.analytic.account'].create({
                    'name': vals.get('name') or _('New Region'),
                    'code': vals.get('code'),
                    'plan_id': plan.id,
                })
                vals['analytic_account_id'] = account.id
        return super().create(vals_list)

    @api.depends('branch_ids')
    def _compute_branch_count(self):
        for region in self:
            region.branch_count = len(region.branch_ids)

    @api.depends('child_ids')
    def _compute_child_region_count(self):
        for region in self:
            region.child_region_count = len(region.child_ids)

    def action_view_regions(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'name': _('Regions / Zones'),
                'res_model': self._name, 'view_mode': 'tree,form',
                'domain': [('parent_id', '=', self.id)],
                'context': {'default_parent_id': self.id, 'default_region_type': 'zone'}}

    @api.constrains('region_type', 'parent_id')
    def _check_arcs_hierarchy(self):
        for region in self:
            if region.region_type == 'hq' and region.parent_id:
                raise ValidationError(_('Headquarters cannot have a parent.'))
            if region.parent_id and region.parent_id.region_type != 'hq':
                raise ValidationError(_('Regions / Zones must report directly to Headquarters.'))
