# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class ArcsDonor(models.Model):
    """A donor (ICRC, IFRC, a national Red Cross/Crescent society, a UN
    agency, the Afghan Government, ...). Mirrors the 'DONORS CODES'
    dimension from the legacy NAV system.

    Paired 1-to-1 with an account.analytic.account on the dedicated
    'ARCS Donor' analytic plan.
    """
    _name = 'arcs.finance.donor'
    _description = 'ARCS Donor'
    _order = 'name'
    _rec_names_search = ['code', 'name']

    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account',
        required=True, ondelete='restrict', copy=False)
    code = fields.Char(related='analytic_account_id.code', store=True, readonly=False)
    name = fields.Char(related='analytic_account_id.name', store=True, readonly=False)
    partner_id = fields.Many2one(
        'res.partner', string='Related Contact',
        help="Optional: link to the donor's contact record if it also exists as a partner.")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('analytic_account_uniq', 'unique(analytic_account_id)',
         'Each analytic account can only be linked to one ARCS donor.'),
    ]

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for donor in self:
            donor.display_name = f"[{donor.code}] {donor.name}" if donor.code else (donor.name or '')

    @api.model_create_multi
    def create(self, vals_list):
        plan = self.env.ref('arcs_finance_data.analytic_plan_donor')
        for vals in vals_list:
            if not vals.get('analytic_account_id'):
                aa = self.env['account.analytic.account'].create({
                    'name': vals.get('name') or _('New Donor'),
                    'code': vals.get('code'),
                    'plan_id': plan.id,
                })
                vals['analytic_account_id'] = aa.id
        return super().create(vals_list)
