EXAMPLE_1C = [
    {  # page 1 question 1
        'answer': '6',
        'id': 7,
        'question_text': 'single page single line text?',
        'section': 1,
        'type': 'SingleLineText',
    },
]

EXAMPLE_2C = {
    'data': {
        'question_7': '6',
    },
    'wizard_form_serialized': [
        [  # step 0 / 1st page
            {  # question 1
                'field_id': 'question_7',
                'id': 7,
                'question_text': '<p>single page single line text?</p>',
                'section': 1,
                'type': 'SingleLineText',
            },
        ]
    ]
}

EXAMPLE_1A = EXAMPLE_SINGLE_QUESTION_Q1_2017 = [
    {  # page 1 question 1
        'answer': '6',
        'choices': [
            {'choice_text': 'radio choice 1', 'id': 1},
            {'choice_text': 'radio choice 2', 'id': 6},
        ],
        'id': 7,
        'question_text': 'which radio choice?',
        'section': 1,
        'type': 'RadioButton',
    },
]

EXAMPLE_2A = EXAMPLE_SINGLE_QUESTION_Q4_2017 = {
    'data': {
        'question_7': '6',
    },
    'wizard_form_serialized': [
        [  # step 0 / 1st page
            {  # question 1
                'choices': [
                    {'extra_info_text': '', 'options': [], 'pk': 1,
                        'position': 0, 'text': 'radio choice 1'},
                    {'extra_info_text': '', 'options': [], 'pk': 6,
                        'position': 1, 'text': 'radio choice 2'},
                ],
                'field_id': 'question_7',
                'id': 7,
                'question_text': '<p>which radio choice?</p>',
                'section': 1,
                'type': 'RadioButton',
            },
        ]
    ]
}

EXAMPLE_1B = EXAMPLE_RECORD_Q1_2017 = [
    {  # page 1 question 1
        'answer': '6',
        'choices': [
            {'choice_text': 'radio choice 1', 'id': 1},
            {'choice_text': 'radio choice 2', 'id': 6},
        ],
        'id': 7,
        'question_text': 'which radio choice?',
        'section': 1,
        'type': 'RadioButton',
    },
    {  # page 1 question 2
        'answer': 'lynncyrin',
        'id': 1,
        'question_text': 'single line text?',
        'section': 1,
        'type': 'SingleLineText',
    },
    {  # page 2 question 3
        'answer': ['7', '12'],
        'choices': [
            {'choice_text': 'radio choice 3', 'id': 2},
            {'choice_text': 'radio choice 4', 'id': 7},
            {'choice_text': 'radio choice 5', 'id': 12},
        ],
        'id': 7,
        'question_text': 'which radio choice? part 2',
        'section': 2,
        'type': 'Checkbox',
    },
    {  # page 2 question 4
        'answer': '',
        'id': 4,
        'question_text': 'multi line text?',
        'section': 3,
        'type': 'MultiLineText',
    },
    {  # page 3 question 5
        'answer': '',
        'id': 5,
        'question_text': 'date field?',
        'section': 4,
        'type': 'Date',
    },
    {  # page 4 question 6
        'answers': [
            [
                {
                    'answer': '',
                    'id': 2,
                    'question_text': "Perpetrator's name (if known)",
                    'section': 4,
                    'type': 'SingleLineText',
                },
                {
                    'answer': '',
                    'id': 3,
                    'question_text': "The Perpetrator's Gender is:",
                    'section': 4,
                    'type': 'SingleLineText',
                },
                {
                    'answer': '',
                    'choices': [
                        {'choice_text': 'USF Undergraduate student', 'id': 3},
                        {'choice_text': 'USF Graduate student', 'id': 8},
                        {'choice_text': 'USF Faculty / staff', 'id': 13},
                        {'choice_text': 'Friend or visitor on campus', 'id': 17},
                        {'choice_text': 'Other', 'id': 20},
                    ],
                    'id': 8,
                    'question_text': "The Perpetrator's Status at the Time Was:",
                    'section': 4,
                    'type': 'RadioButton',
                },
            ],
        ],
        'page_id': 3,
        'prompt': 'perpetrator',
        'section': 4,
        'type': 'FormSet',
    },
]

EXAMPLE_2B = EXAMPLE_RECORD_Q4_2017 = {
    'data': {
        'question_7': '6',
        'question_1': 'lynncyrin',
        'question_387': '',
        'question_898': ['2414', '2415'],
        'question_919': 'lynncyrin',
        'question_920': '',
        'question_954': '',
    },
    'wizard_form_serialized': [
        [  # step 0 / 1st page
            {  # question 1
                'choices': [
                    {'extra_info_text': '', 'options': [], 'pk': 1,
                        'position': 0, 'text': 'radio choice 1'},
                    {'extra_info_text': '', 'options': [], 'pk': 6,
                        'position': 1, 'text': 'radio choice 2'},
                ],
                'field_id': 'question_7',
                'id': 7,
                'question_text': '<p>which radio choice?</p>',
                'section': 1,
                'type': 'RadioButton',
            },
            {  # question 2
                'field_id': 'question_1',
                'id': 1,
                'question_text': '<p>single line text?</p>',
                'section': 1,
                'type': 'SingleLineText',
            },
        ],
        [  # step 1 / 2nd page
            {  # question 3
                'choices': [
                    {'extra_info_text': '', 'options': [],
                        'pk': 2411, 'position': 0, 'text': 'Other'},
                    {'extra_info_text': '', 'options': [], 'pk': 2406,
                        'position': 1, 'text': 'This school year (since August)'},
                ],
                'field_id': 'question_7',
                'id': 7,
                'question_text': '<p>When did it happen?</p>',
                'section': 1,
                'type': 'Radiobutton'
            },
            {  # question 4
                'field_id': 'question_1',
                'id': 952,
                'question_text': '<p>If you know the exact date, please place it here. (MM/DD/YYYY)</p>',
                'section': 1,
                'type': 'Singlelinetext',
            },
        ],
    ],
}
