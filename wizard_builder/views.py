from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect, JsonResponse
from django.views.generic.edit import FormView

from .forms import PageFormManager

# from django-formtools
# Portions of the below implementation are copyright theDjango Software Foundation and individual contributors, and
# are under the BSD-3 Clause License:
# https://github.com/django/django-formtools/blob/master/LICENSE


class StepsHelper(object):
    done_name = 'done'

    def __init__(self, view):
        self.view = view

    @property
    def all(self):
        return self.view.form_manager.forms

    @property
    def step_count(self):
        return len(self.all)

    @property
    def current(self):
        _step = self._current or self.first
        if _step == self.done_name:
            return _step
        elif _step <= self.last:
            return _step
        else:
            return self.last

    @property
    def _current(self):
        _step = self.view.request.session.get('current_step', self.first)
        if _step == self.done_name:
            return _step
        else:
            return int(_step)

    @property
    def _goto_step_submit(self):
        return self.view.request.POST.get('wizard_goto_step', None) == 'Submit'

    @property
    def first(self):
        return 0

    @property
    def last(self):
        return self.all[-1].page_index

    @property
    def next(self):
        return self.adjust_step(1)

    @property
    def prev(self):
        return self.adjust_step(0)

    @property
    def next_is_done(self):
        return self.next == self.done_name

    @property
    def current_is_done(self):
        return self.current == self.done_name

    @property
    def current_url(self):
        return self.url(self.current)

    @property
    def done_url(self):
        return self.url(self.done_name)

    def url(self, step):
        return reverse(
            self.view.request.resolver_match.view_name,
            kwargs={'step': step},
        )

    def finished(self, step):
        return self._goto_step_submit or step == self.done_name

    def set_from_get(self, step_url_param):
        step = step_url_param or self.current
        self.view.request.session['current_step'] = step

    def set_from_post(self):
        step = self.view.request.POST.get('wizard_current_step', self.current)
        if self.view.request.POST.get('wizard_goto_step', None) == 'Back':
            step = self.adjust_step(-1)
        if self.view.request.POST.get('wizard_goto_step', None) == 'Next':
            step = self.adjust_step(1)
        self.view.request.session['current_step'] = step

    def adjust_step(self, adjustment):
        key = self.current + adjustment
        if key < self.first:
            return None
        if key == self.first:
            return self.first
        elif self.step_count > key:
            return self.view.form_manager.forms[key].page_index
        elif self.step_count == key:
            return self.done_name
        else:
            return None


class StorageHelper(object):

    def __init__(self, view):
        self.view = view

    @property
    def get_form_data(self):
        return {'data': [
            self.view.request.session[self.session_key(form.page_index)]
            for form in self.view.form_manager.forms
        ]}

    def session_key(self, step):
        return 'wizard_page_index_{}'.format(step)

    def set_form_data(self, form):
        key = self.session_key(form.page_index)
        self.view.request.session[key] = form.processed


class WizardView(FormView):
    site_id = None
    url_name = None
    template_name = 'wizard_builder/wizard_form.html'

    @property
    def steps(self):
        return StepsHelper(self)

    @property
    def storage(self):
        return StorageHelper(self)

    @property
    def form_manager(self):
        return PageFormManager(get_current_site(self.request).id)

    def get_form(self):
        return self.form_manager.forms[self.steps.current]

    def dispatch(self, request, step=None, *args, **kwargs):
        self.steps.set_from_get(step)
        if self.steps.finished(step):
            return self.render_done(**kwargs)
        else:
            return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.steps.set_from_post()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form, **kwargs):
        self.storage.set_form_data(form)
        return self.render_step(**kwargs)

    def render_step(self, **kwargs):
        return HttpResponseRedirect(self.steps.current_url)

    def render_done(self, **kwargs):
        if self.steps.current_is_done:
            # TODO: a review screen template
            return JsonResponse(self.storage.get_form_data)
        else:
            return HttpResponseRedirect(self.steps.done_url)
