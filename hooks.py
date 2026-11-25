from odoo import _
from odoo.exceptions import UserError
from odoo.tools import convert_file


SEED_FILES = (
    "data/analytic_plan_data.xml",
    "data/arcs_finance_region_data.xml",
    "data/arcs_branch_data.xml",
    "data/arcs_donor_data.xml",
    "data/arcs_finance_program_data.xml",
    "data/arcs_finance_project_data.xml",
    "data/arcs_activity_data.xml",
)

SHARED_PLANS = ("region", "branch", "donor", "project", "activity")


def _upgrading_finance(env):
    return env['ir.module.module'].search_count([
        ('name', '=', 'arcs_finance'),
        ('state', 'in', ('installed', 'to upgrade')),
    ], limit=1)


def pre_init_hook(env):
    if _upgrading_finance(env):
        for plan in SHARED_PLANS:
            legacy = env.ref(f"arcs_finance.analytic_plan_{plan}", raise_if_not_found=False)
            transferred = env.ref(f"arcs_finance_data.analytic_plan_{plan}", raise_if_not_found=False)
            if not legacy or legacy != transferred:
                raise UserError(_("Run the ARCS finance suite pre-upgrade script before installing shared data."))


def post_init_hook(env):
    if _upgrading_finance(env):
        # The versioned migration keeps existing data and also respects records
        # deliberately removed by the customer after their initial installation.
        return
    idref = {}
    for path in SEED_FILES:
        convert_file(env, "arcs_finance_data", path, idref, mode="init")
