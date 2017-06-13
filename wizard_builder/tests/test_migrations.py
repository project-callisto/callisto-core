from django_migration_testcase import MigrationTest


class SitesMigrationTest(MigrationTest):

    app_name = 'wizard_builder'
    before = '0005_delete_constraints'
    after = '0006_many_sites'

    def test_sites_attribute_populated(self):
        OldPageBase = self.get_model_before('wizard_builder.PageBase')
        old_page = OldPageBase.objects.create(site_id=1)

        self.run_migration()
        NewPageBase = self.get_model_after('wizard_builder.PageBase')
        new_page = NewPageBase.objects.first()

        self.assertEqual(old_page.site_id, new_page.sites.first().id)

    def test_phantom_sites_not_populated(self):
        OldPageBase = self.get_model_before('wizard_builder.PageBase')
        old_page = OldPageBase.objects.create()

        self.run_migration()
        NewPageBase = self.get_model_after('wizard_builder.PageBase')
        new_page = NewPageBase.objects.first()

        self.assertEqual(old_page.site_id, None)
        self.assertEqual(new_page.sites.count(), 0)
