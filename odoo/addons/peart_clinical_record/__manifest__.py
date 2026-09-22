{
    'name': 'Peart Serenity - Clinical Record',
    'version': '19.0.1.0.0',
    'category': 'Services/Care Management',
    'summary': 'Resident file, clinical history, daily care log and family access',
    'description': """
Peart Serenity - Clinical Record
================================

Phase 1 (foundation) and phase 2 (clinical history):

- Resident file (peart.resident), created from an admitted care admission.
- Clinical roles: Doctor, Nurse, Administrator, CEO (read-only).
- Family access: a portal user only sees a resident when an explicit,
  active family link exists AND a family-access consent has been recorded.
- Consent register (Data Protection Act 2020 - health data is sensitive).

Phase 2 adds intake, diagnoses, allergies, medication orders, care plan,
documents and data-driven assessment scales (Barthel, Katz, Morse, Norton,
SPMSQ, GDS-15) with automatic scoring.

Phase 3 adds the two-shift daily log with vital-sign flags, the medication
administration record (MAR) and incident reports.

Later phases add the family portal and the ARIA family assistant.
""",
    'author': 'Peart Serenity Residence',
    'license': 'LGPL-3',
    'depends': ['peart_serenity', 'mail', 'portal', 'ai_agent_core'],
    'data': [
        'security/clinical_security.xml',
        'security/ir.model.access.csv',
        'security/clinical_rules.xml',
        'data/sequence_data.xml',
        'data/activity_data.xml',
        'data/ai_clinical_agent_data.xml',
        'data/handover_cron_data.xml',
        'data/ai_clinical_action_tools_data.xml',
        'data/scale_data.xml',
        'views/peart_resident_views.xml',
        'views/peart_clinical_views.xml',
        'views/peart_care_views.xml',
        'views/peart_admission_views.xml',
        'views/peart_clinical_assistant_wizard_views.xml',
        'views/peart_family_note_draft_wizard_views.xml',
        'views/res_config_settings_views.xml',
        'views/peart_shift_handover_views.xml',
        'views/peart_clinical_action_request_views.xml',
        'views/peart_nursing_task_wizard_views.xml',
        'views/report_templates.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.report_assets_common': ['peart_clinical_record/static/src/css/clinical_report.css'],
        'web.report_assets_pdf': ['peart_clinical_record/static/src/css/clinical_report.css'],
    },
    'installable': True,
    'application': True,
}
