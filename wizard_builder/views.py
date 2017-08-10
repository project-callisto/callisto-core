from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic.edit import FormView
from django.http import JsonResponse
from django.contrib.sites.shortcuts import get_current_site

from .forms import PageFormManager, PageForm
from .storage import SessionStorage
from .models import Page

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
        return self._current or self.first

    @property
    def _current(self):
        return int(self.view.request.session.get('current_step', 0))

    @property
    def finished(self):
        return self.view.request.POST.get('wizard_goto_step', None) == 'Submit'

    @property
    def first(self):
        return 0

    @property
    def last(self):
        return self.all[-1].page_index

    @property
    def next(self):
        return self.step_key(1)

    @property
    def prev(self):
        return self.step_key(-1)

    @property
    def next_is_done(self):
        return self.next == self.done_name

    def set_from_get(self):
        step = self.view.request.GET.get('step', None)
        if step:
            self.view.request.session['current_step'] = step

    def set_from_post(self):
        step = self.view.request.POST.get('wizard_current_step', None)
        if step:
            self.view.request.session['current_step'] = step

    def advance(self):
        self.request.session['current_step'] = self.steps.next

    def step_key(self, adjustment):
        key = self.current + adjustment
        if self.step_count > key:
            return self.view.forms[key].page_index
        elif self.step_count == key:
            return self.done_name
        else:
            return None


class StorageMixin(object):

    def set_form_data(self, form):
        self.request.session['wizard'][self.steps.current] = form.data

    @property
    def get_form_data(self):
        return self.request.session['wizard']


class WizardView(StorageMixin, FormView):
    site_id = None
    url_name = None
    template_name = 'wizard_builder/wizard_form.html'

    @property
    def steps(self):
        return StepsHelper(self)

    @property
    def form_manager(self):
        return PageFormManager(get_current_site(self.request).id)

    @property
    def form(self):
        return self.get_form()

    @property
    def forms(self):
        return self.form_manager.forms

    def get_form(self):
        return self.forms[self.steps.current]

    def get(self, request, *args, **kwargs):
        self.steps.set_from_get()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.steps.set_from_post()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form, **kwargs):
        self.steps.advance()
        self.set_form_data(form)
        self.render()

    def render(self, **kwargs):
        if self.steps.finished:
            return self.render_done(**kwargs)
        else:
            return super().render(**kwargs)

    def render_done(self, **kwargs):
        return JsonResponse(self.get_form_data)
