from django_migration_testcase import MigrationTest


class SitesMigrationTest(MigrationTest):

    app_name = 'wizard_builder'
    before = '0005_delete_constraints'
    after = '0006_many_sites'

    def test_sites_attribute_populated(self):
        OldQuestionPage = self.get_model_before('wizard_builder.QuestionPage')
        old_page = OldQuestionPage.objects.create(site_id=1)

        self.run_migration()
        NewQuestionPage = self.get_model_after('wizard_builder.QuestionPage')
        new_page = NewQuestionPage.objects.first()

        self.assertEqual(old_page.site_id, new_page.sites.first().id)

    def test_phantom_sites_not_populated(self):
        OldQuestionPage = self.get_model_before('wizard_builder.QuestionPage')
        old_page = OldQuestionPage.objects.create()

        self.run_migration()
        NewQuestionPage = self.get_model_after('wizard_builder.QuestionPage')
        new_page = NewQuestionPage.objects.first()

        self.assertEqual(old_page.site_id, None)
        self.assertEqual(new_page.sites.count(), 0)


class QuestionPageMigrationTest(MigrationTest):

    app_name = 'wizard_builder'
    before = '0008_remove_textpage'
    after = '0011_rename_questionpage_attrs'

    def test_attributes_populated(self):
        OldQuestionPage = self.get_model_before('wizard_builder.QuestionPage')
        old_page = OldQuestionPage.objects.create(
            position=20,
            section=1,
        )
        old_page.sites.add(1)
        old_page_sites_count = old_page.sites.count()

        self.run_migration()
        NewQuestionPage = self.get_model_after('wizard_builder.QuestionPage')
        new_page = NewQuestionPage.objects.first()
        new_page_sites_count = new_page.sites.count()

        self.assertEqual(old_page.section, new_page.section)
        self.assertEqual(old_page.position, new_page.position)
        self.assertEqual(old_page_sites_count, new_page_sites_count)


class PageIDMigrationTest(MigrationTest):

    app_name = 'wizard_builder'
    before = '0011_rename_questionpage_attrs'
    after = '0014_questionpage_to_page_3'

    def _get_attrs(self, cls, attr):
        return list(cls.objects.all().values_list(attr, flat=True))

    def test_attributes_populated(self):
        OldQuestionPage = self.get_model_before('wizard_builder.QuestionPage')
        for i in range(3):
            OldQuestionPage.objects.create()
        old_page_ids = self._get_attrs(OldQuestionPage, 'pagebase_ptr_id')

        self.run_migration()
        NewPage = self.get_model_after('wizard_builder.Page')
        new_page_ids = self._get_attrs(NewPage, 'id')

        self.assertCountEqual(old_page_ids, new_page_ids)
