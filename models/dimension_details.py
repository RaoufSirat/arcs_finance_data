from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class AnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'
    serial_no = fields.Char(string='Serial No.', index=True, copy=False)

    def write(self, vals):
        protected = {'code', 'name', 'company_id', 'plan_id'}
        if (protected.intersection(vals) and not self.env.su
                and not self.env.user.has_group('arcs_finance_data.group_master_data_manager')):
            linked_models = (
                'arcs.finance.region', 'arcs.finance.branch', 'arcs.finance.donor',
                'arcs.finance.program', 'arcs.finance.project', 'arcs.finance.activity',
            )
            # Use elevated access only for the existence check so standard
            # Accounting users cannot bypass master-data permissions.
            domain = [('analytic_account_id', 'in', self.ids)]
            if any(self.env[model].sudo().with_context(active_test=False).search_count(domain, limit=1)
                   for model in linked_models):
                raise AccessError(_('Only an ARCS Master Data Manager can change shared ARCS identifiers.'))
        return super().write(vals)


class Programme(models.Model):
    _inherit = 'arcs.finance.program'
    serial_no = fields.Char(string='Serial No.', index=True, copy=False)
    # Same relation table, reversed columns: edits from either end are symmetric.
    project_ids = fields.Many2many(
        'arcs.finance.project', 'arcs_program_project_rel', 'program_id', 'project_id',
        string='Projects')
    activity_ids = fields.Many2many(
        'arcs.finance.activity', 'arcs_program_activity_rel', 'program_id', 'activity_id',
        string='Activities')


class Project(models.Model):
    _inherit = 'arcs.finance.project'
    serial_no = fields.Char(string='Serial No.', index=True, copy=False)
    program_ids = fields.Many2many(
        'arcs.finance.program', 'arcs_program_project_rel', 'project_id', 'program_id',
        string='Programmes')
    activity_ids = fields.Many2many(
        'arcs.finance.activity', 'arcs_project_activity_rel', 'project_id', 'activity_id',
        string='Activities')

    @api.depends('name')
    def _compute_complete_name(self):
        for project in self:
            project.complete_name = project.name

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records.filtered('program_id'):
            record.program_ids = [fields.Command.link(record.program_id.id)]
        return records

    def write(self, vals):
        result = super().write(vals)
        # Retain compatibility with old imports; legacy primary is never used
        # for filtering, accounting, or permissions in this release.
        if vals.get('program_id'):
            self.write({'program_ids': [fields.Command.link(vals['program_id'])]})
        return result


class Activity(models.Model):
    _inherit = 'arcs.finance.activity'
    serial_no = fields.Char(string='Serial No.', index=True, copy=False)
    project_ids = fields.Many2many(
        'arcs.finance.project', 'arcs_project_activity_rel', 'activity_id', 'project_id',
        string='Projects')
    program_ids = fields.Many2many(
        'arcs.finance.program', 'arcs_program_activity_rel', 'activity_id', 'program_id',
        string='Programmes')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records.filtered('project_id'):
            record.project_ids = [fields.Command.link(record.project_id.id)]
        return records

    def write(self, vals):
        result = super().write(vals)
        if vals.get('project_id'):
            self.write({'project_ids': [fields.Command.link(vals['project_id'])]})
        return result


class Donor(models.Model):
    _inherit = 'arcs.finance.donor'
    serial_no = fields.Char(string='Serial No.', index=True, copy=False)
