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


class PopulateTypeMigrationTest(MigrationTest):

    app_name = 'wizard_builder'
    before = '0028_formquestion_type'
    after = '0029_populate_type'

    def test_type_populated(self):
        FormQuestion = self.get_model_before('wizard_builder.FormQuestion')
        RadioButton = self.get_model_before('wizard_builder.RadioButton')
        Checkbox = self.get_model_before('wizard_builder.Checkbox')
        TextArea = self.get_model_before('wizard_builder.TextArea')
        SingleLineText = self.get_model_before('wizard_builder.SingleLineText')

        formquestion = FormQuestion.objects.create()
        radiobutton = RadioButton.objects.create()
        checkbox = Checkbox.objects.create()
        textarea = TextArea.objects.create()
        singlelinetext = SingleLineText.objects.create()

        self.run_migration()

        self.assertEqual(
            FormQuestion.objects.get(id=formquestion.id).type,
            None,
        )
        self.assertEqual(
            FormQuestion.objects.get(id=radiobutton.id).type,
            'radiobutton',
        )
        self.assertEqual(
            FormQuestion.objects.get(id=checkbox.id).type,
            'checkbox',
        )
        self.assertEqual(
            FormQuestion.objects.get(id=textarea.id).type,
            'textarea',
        )
        self.assertEqual(
            FormQuestion.objects.get(id=singlelinetext.id).type,
            'singlelinetext',
        )


class PopulateDropdownMigrationTest(MigrationTest):

    app_name = 'wizard_builder'
    before = '0031_formquestion_choices_default'
    after = '0032_move_question_dropdown'

    def test_type_populated(self):
        RadioButton = self.get_model_before('wizard_builder.RadioButton')

        yes_dropdown = RadioButton.objects.create(is_dropdown=True)
        no_dropdown = RadioButton.objects.create()

        self.run_migration()

        FormQuestion = self.get_model_after('wizard_builder.FormQuestion')
        yes_question_id = yes_dropdown.formquestion_ptr.id
        no_question_id = no_dropdown.formquestion_ptr.id

        self.assertEqual(
            FormQuestion.objects.get(id=yes_question_id).is_dropdown,
            True,
        )
        self.assertEqual(
            FormQuestion.objects.get(id=no_question_id).is_dropdown,
            False,
        )


class MoveChoiceQuestionMigrationTest(MigrationTest):

    app_name = 'wizard_builder'
    before = '0033_add_temps'
    after = '0034_move_choice_question'

    def test_type_populated(self):
        RadioButton = self.get_model_before('wizard_builder.RadioButton')
        OldChoice = self.get_model_before('wizard_builder.Choice')

        question = RadioButton.objects.create()
        old_choice = OldChoice.objects.create(question=question)
        old_base_question = old_choice.question.formquestion_ptr

        self.run_migration()

        NewChoice = self.get_model_after('wizard_builder.Choice')
        new_choice = NewChoice.objects.get(id=old_choice.id)
        new_base_question = new_choice.question

        self.assertEqual(
            old_base_question._meta.model_name.lower(), 'formquestion')
        self.assertEqual(
            new_base_question._meta.model_name.lower(), 'formquestion')
        self.assertEqual(
            old_base_question.id, new_base_question.id)
