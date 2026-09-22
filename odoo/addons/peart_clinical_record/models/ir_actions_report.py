from odoo import models

AUDITED_REPORTS = ('peart_clinical_record.report_resident_record_document',)


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        report = self._get_report(report_ref)
        if report.report_name in AUDITED_REPORTS and res_ids:
            for resident in self.env['peart.resident'].browse(res_ids):
                self.env['peart.family.access.log'].sudo().create({
                    'user_id': self.env.user.id, 'resident_id': resident.id,
                    'action': 'report', 'detail': report.name})
        return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)
