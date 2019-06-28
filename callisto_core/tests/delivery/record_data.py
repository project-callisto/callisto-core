EXAMPLE_SINGLE_LINE = [
    {  # page 1 question 1
        "answer": "6",
        "id": 7,
        "question_text": "single page single line text?",
        "section": 1,
        "type": "SingleLineText",
    }
]

EXPECTED_SINGLE_LINE = {
    "data": {"question_7": "6"},
    "wizard_form_serialized": [
        [  # step 0 / 1st page
            {  # question 1
                "field_id": "question_7",
                "id": 7,
                "question_text": "<p>single page single line text?</p>",
                "section": 1,
                "type": "SingleLineText",
            }
        ]
    ],
}

EXAMPLE_SINGLE_RADIO = [
    {  # page 1 question 1
        "answer": "6",
        "choices": [
            {"choice_text": "radio choice 1", "id": 1},
            {"choice_text": "radio choice 2", "id": 6},
        ],
        "id": 7,
        "question_text": "which radio choice?",
        "section": 1,
        "type": "RadioButton",
    }
]

EXPECTED_SINGLE_RADIO = {
    "data": {"question_7": "6"},
    "wizard_form_serialized": [
        [  # step 0 / 1st page
            {  # question 1
                "choices": [
                    {
                        "extra_info_text": "",
                        "options": [],
                        "pk": 1,
                        "position": 0,
                        "text": "radio choice 1",
                    },
                    {
                        "extra_info_text": "",
                        "options": [],
                        "pk": 6,
                        "position": 0,
                        "text": "radio choice 2",
                    },
                ],
                "field_id": "question_7",
                "id": 7,
                "question_text": "<p>which radio choice?</p>",
                "section": 1,
                "type": "RadioButton",
            }
        ]
    ],
}

EXAMPLE_FORMSET = [
    {  # page 1 question 1
        "answer": "",
        "id": 5,
        "question_text": "date field?",
        "section": 1,
        "type": "Date",
    },
    {  # page 2
        "answers": [
            [
                {  # question 2
                    "answer": "",
                    "id": 2,
                    "question_text": "perp name:",
                    "section": 2,
                    "type": "SingleLineText",
                },
                {  # question 3
                    "answer": "",
                    "id": 3,
                    "question_text": "perp gender:",
                    "section": 2,
                    "type": "SingleLineText",
                },
                {  # question 4
                    "answer": "",
                    "choices": [
                        {"choice_text": "undergrad", "id": 3},
                        {"choice_text": "grad", "id": 8},
                    ],
                    "id": 8,
                    "question_text": "prep status:",
                    "section": 2,
                    "type": "RadioButton",
                },
            ]
        ],
        "page_id": 3,
        "prompt": "perpetrator",
        "section": 2,
        "type": "FormSet",
    },
]

EXPECTED_FORMSET = {
    "data": {"question_5": "", "question_2": "", "question_3": "", "question_8": ""},
    "wizard_form_serialized": [
        [  # step 0 / 1st page
            {  # question 1
                "field_id": "question_5",
                "id": 5,
                "question_text": "<p>date field?</p>",
                "section": 1,
                "type": "Date",
            }
        ],
        [  # step 1 / 2nd page
            {  # question 2
                "field_id": "question_2",
                "id": 2,
                "question_text": "<p>perp name:</p>",
                "section": 2,
                "type": "SingleLineText",
                "group": "FormSet",
            },
            {  # question 3
                "field_id": "question_3",
                "id": 3,
                "question_text": "<p>perp gender:</p>",
                "section": 2,
                "type": "SingleLineText",
                "group": "FormSet",
            },
            {  # question 4
                "choices": [
                    {
                        "extra_info_text": "",
                        "options": [],
                        "pk": 3,
                        "position": 0,
                        "text": "undergrad",
                    },
                    {
                        "extra_info_text": "",
                        "options": [],
                        "pk": 8,
                        "position": 0,
                        "text": "grad",
                    },
                ],
                "field_id": "question_8",
                "id": 8,
                "question_text": "<p>prep status:</p>",
                "section": 2,
                "type": "RadioButton",
                "group": "FormSet",
            },
        ],
    ],
}

EXAMPLE_FULL_DATASET = [
    {
        "answer": "example data",
        "id": 1,
        "question_text": "Write it down",
        "section": 2,
        "type": "SingleLineText",
    },
    {
        "answer": "1",
        "choices": [
            {"choice_text": "Within the last 5 days", "id": 1},
            {"choice_text": "More than 5 days ago", "id": 6},
            {"choice_text": "Other/I'm not sure", "id": 11},
        ],
        "id": 7,
        "question_text": "How recent was it?",
        "section": 3,
        "type": "RadioButton",
    },
    {
        "answer": "example data",
        "id": 4,
        "question_text": "What happened?",
        "section": 3,
        "type": "MultiLineText",
    },
    {
        "answer": "example data",
        "id": 5,
        "question_text": "When did it happen?",
        "section": 3,
        "type": "Date",
    },
    {
        "answer": ["2", "16"],
        "choices": [
            {
                "choice_text": "I have physical evidence - clothing, bedsheets, other objects with possible DNA",
                "id": 2,
            },
            {
                "choice_text": "I have electronic evidence - emails, text messages, photos, social media interactions",
                "id": 7,
            },
            {
                "choice_text": "I don't have any evidence (that's totally fine)",
                "id": 12,
            },
            {"choice_text": "Other / I'm not sure", "id": 16},
        ],
        "id": 6,
        "question_text": "Is there any evidence you can save?",
        "section": 3,
        "type": "Checkbox",
    },
    {
        "answer": "4",
        "choices": [
            {"choice_text": "First choice", "id": 4},
            {"choice_text": "Second choice", "id": 9},
            {"choice_text": "Third choice", "id": 14},
            {"choice_text": "Other ", "id": 18},
        ],
        "id": 9,
        "question_text": "Test question with field for more info",
        "section": 3,
        "type": "RadioButton",
    },
    {
        "answer": "15",
        "choices": [
            {"choice_text": "Main (Lone Mountain)", "id": 5},
            {"choice_text": "Downtown SF", "id": 10},
            {"choice_text": "Pleasanton", "id": 15},
            {"choice_text": "Sacramento", "id": 19},
            {"choice_text": "San Jose", "id": 21},
            {"choice_text": "Santa Rosa", "id": 22},
        ],
        "id": 10,
        "question_text": "What campus do you attend?",
        "section": 3,
        "type": "RadioButton",
    },
    {
        "answers": [
            [
                {
                    "answer": "1 example data",
                    "id": 2,
                    "question_text": "Perpetrator's name (if known)",
                    "section": 4,
                    "type": "SingleLineText",
                },
                {
                    "answer": "1 example data",
                    "id": 3,
                    "question_text": "The Perpetrator's Gender is:",
                    "section": 4,
                    "type": "SingleLineText",
                },
                {
                    "answer": "17",
                    "choices": [
                        {"choice_text": "USF Undergraduate student", "id": 3},
                        {"choice_text": "USF Graduate student", "id": 8},
                        {"choice_text": "USF Faculty / staff", "id": 13},
                        {"choice_text": "Friend or visitor on campus", "id": 17},
                        {"choice_text": "Other", "id": 20},
                    ],
                    "id": 8,
                    "question_text": "The Perpetrator's Status at the Time Was:",
                    "section": 4,
                    "type": "RadioButton",
                },
            ],
            [
                {
                    "answer": "2 example data",
                    "id": 2,
                    "question_text": "Perpetrator's name (if known)",
                    "section": 4,
                    "type": "SingleLineText",
                },
                {
                    "answer": "2 example data",
                    "id": 3,
                    "question_text": "The Perpetrator's Gender is:",
                    "section": 4,
                    "type": "SingleLineText",
                },
                {
                    "answer": "3",
                    "choices": [
                        {"choice_text": "USF Undergraduate student", "id": 3},
                        {"choice_text": "USF Graduate student", "id": 8},
                        {"choice_text": "USF Faculty / staff", "id": 13},
                        {"choice_text": "Friend or visitor on campus", "id": 17},
                        {"choice_text": "Other", "id": 20},
                    ],
                    "id": 8,
                    "question_text": "The Perpetrator's Status at the Time Was:",
                    "section": 4,
                    "type": "RadioButton",
                },
            ],
        ],
        "page_id": 3,
        "prompt": "perpetrator",
        "section": 4,
        "type": "FormSet",
    },
]
