import logging
from copy import copy

from django.core.urlresolvers import reverse

from . import managers
from .data_helper import SerializedDataHelper

logger = logging.getLogger(__name__)


class StepsHelper(object):
    done_name = 'done'
    review_name = 'Review'
    next_name = 'Next'
    back_name = 'Back'
    wizard_goto_name = 'wizard_goto_step'
    wizard_current_name = 'wizard_current_step'
    wizard_form_fields = [
        wizard_current_name,
        wizard_goto_name,
    ]

    def __init__(self, view):
        self.view = view

    @property
    def step_count(self):
        return len(self.view.forms)

    @property
    def current(self):
        step = getattr(self.view, 'curent_step', 0)
        if isinstance(step, str):
            return step
        elif step <= self.last:
            return step
        else:
            return self.last

    @property
    def last(self):
        return self.step_count - 1

    @property
    def next(self):
        return self.adjust_step(1)

    @property
    def next_is_done(self):
        if isinstance(self.current, int):
            return self.next == self.done_name
        else:
            return False

    @property
    def current_is_done(self):
        return self.current == self.done_name

    @property
    def current_url(self):
        return self.url(self.current)

    @property
    def first_url(self):
        return self.url(0)

    @property
    def last_url(self):
        return self.url(self.last)

    @property
    def done_url(self):
        return self.url(self.done_name)

    @property
    def _goto_step_back(self):
        return self._goto_step(self.back_name)

    @property
    def _goto_step_next(self):
        return self._goto_step(self.next_name)

    @property
    def _goto_step_review(self):
        return self._goto_step(self.review_name)

    def parse_step(self, step):
        if step == self.done_name:
            return step
        else:
            return int(step)

    def url(self, step):
        return reverse(
            self.view.request.resolver_match.view_name,
            kwargs={'step': step},
        )

    def overflowed(self, step):
        return int(step) > int(self.last)

    def finished(self, step):
        return self._goto_step_review or step == self.done_name

    def set_from_post(self):
        if self._goto_step_back:
            self.view.curent_step = self.adjust_step(-1)
        if self._goto_step_next:
            self.view.curent_step = self.adjust_step(1)

    def adjust_step(self, adjustment):
        step = self.view.curent_step + adjustment
        if step >= self.step_count:
            return self.done_name
        else:
            return step

    def _goto_step(self, step_type):
        post = self.view.request.POST
        return post.get(self.wizard_goto_name, None) == step_type


class StorageHelper(object):
    data_manager = SerializedDataHelper
    form_manager = managers.FormManager
    storage_data_key = 'wizard_form_data'
    storage_form_key = 'wizard_form_serialized'

    def __init__(self, view):
        # TODO: scope down inputs
        self.view = view
        self.site_id = view.get_site_id()
        self.session = view.request.session
        self.init_storage()

    @property
    def cleaned_form_data(self):
        storage = self.current_data_from_storage()
        return self.data_manager.get_zipped_data(
            data=storage[self.storage_data_key],
            forms=storage[self.storage_form_key],
        )

    @property
    def answers_for_current_step(self):
        # get the current data
        data = self.current_data_from_storage()
        # create a set of forms from form storage + post data
        new_data = copy(data)
        new_data[self.storage_data_key] = self.view.request.POST
        forms = self.get_form_models(new_data)
        # get the cleaned data from those forms, add it to answer data
        form = forms[self.view.curent_step]
        data[self.storage_data_key].update(form.cleaned_data)
        # return answer data
        return data[self.storage_data_key]

    @property
    def serialized_forms(self):
        return self.form_manager.get_serialized_forms(site_id=self.site_id)

    def get_form_models(self, data=None):
        if not data:
            data = self.current_data_from_storage()
        return self.form_manager.get_form_models(
            form_data=data[self.storage_form_key],
            answer_data=data[self.storage_data_key],
            site_id=self.site_id,
        )

    def update(self):
        '''
        primary class functionality method, updates the data in storage
        '''
        self.add_data_to_storage(self.answers_for_current_step)

    def current_data_from_storage(self):
        return {
            self.storage_data_key: self.session.get(self.storage_data_key, {}),
            self.storage_form_key: self.session.get(self.storage_form_key, {}),
        }

    def add_data_to_storage(self, answer_data):
        self.session[self.storage_data_key] = answer_data

    def init_storage(self):
        self.session.setdefault(
            self.storage_form_key,
            self.serialized_forms,
        )
        self.session.setdefault(
            self.storage_data_key,
            {},
        )


class WizardViewTemplateHelpers(object):
    # TODO: these sould all be context variables instead

    @property
    def wizard_prev_step_exists(self):
        return self.steps.current

    @property
    def wizard_next_is_done(self):
        return self.steps.next_is_done

    @property
    def wizard_current_step(self):
        return self.steps.current

    @property
    def wizard_goto_name(self):
        return self.steps.wizard_goto_name

    @property
    def wizard_current_name(self):
        return self.steps.wizard_current_name

    @property
    def wizard_review_name(self):
        return self.steps.review_name

    @property
    def wizard_next_name(self):
        return self.steps.next_name

    @property
    def wizard_back_name(self):
        return self.steps.back_name
