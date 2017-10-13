EXAMPLE_SINGLE_LINE = [
    {  # page 1 question 1
        'answer': '6',
        'id': 7,
        'question_text': 'single page single line text?',
        'section': 1,
        'type': 'SingleLineText',
    },
]

EXPECTED_SINGLE_LINE = {
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

EXAMPLE_SINGLE_RADIO = [
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

EXPECTED_SINGLE_RADIO = {
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
                        'position': 0, 'text': 'radio choice 2'},
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

EXAMPLE_FORMSET = [
    {  # page 1 question 1
        'answer': '',
        'id': 5,
        'question_text': 'date field?',
        'section': 1,
        'type': 'Date',
    },
    {  # page 2
        'answers': [
            [
                {  # question 2
                    'answer': '',
                    'id': 2,
                    'question_text': 'perp name:',
                    'section': 2,
                    'type': 'SingleLineText',
                },
                {  # question 3
                    'answer': '',
                    'id': 3,
                    'question_text': 'perp gender:',
                    'section': 2,
                    'type': 'SingleLineText',
                },
                {  # question 4
                    'answer': '',
                    'choices': [
                        {'choice_text': 'undergrad', 'id': 3},
                        {'choice_text': 'grad', 'id': 8},
                    ],
                    'id': 8,
                    'question_text': 'prep status:',
                    'section': 2,
                    'type': 'RadioButton',
                },
            ],
        ],
        'page_id': 3,
        'prompt': 'perpetrator',
        'section': 2,
        'type': 'FormSet',
    },
]

EXPECTED_FORMSET = {
    'data': {
        'question_5': '',
        'question_2': '',
        'question_3': '',
        'question_8': '',
    },
    'wizard_form_serialized': [
        [  # step 0 / 1st page
            {  # question 1
                'field_id': 'question_5',
                'id': 5,
                'question_text': '<p>date field?</p>',
                'section': 1,
                'type': 'Date',
            },
        ],
        [  # step 1 / 2nd page
            {  # question 2
                'field_id': 'question_2',
                'id': 2,
                'question_text': '<p>perp name:</p>',
                'section': 2,
                'type': 'SingleLineText',
                'group': 'FormSet',
            },
            {  # question 3
                'field_id': 'question_3',
                'id': 3,
                'question_text': '<p>perp gender:</p>',
                'section': 2,
                'type': 'SingleLineText',
                'group': 'FormSet',
            },
            {  # question 4
                'choices': [
                    {'extra_info_text': '', 'options': [],
                        'pk': 3, 'position': 0, 'text': 'undergrad'},
                    {'extra_info_text': '', 'options': [],
                        'pk': 8, 'position': 0, 'text': 'grad'},
                ],
                'field_id': 'question_8',
                'id': 8,
                'question_text': '<p>prep status:</p>',
                'section': 2,
                'type': 'RadioButton',
                'group': 'FormSet',
            },
        ],
    ],
}
