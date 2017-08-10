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
        _current = self._current or self.first
        if _current <= self.last:
            return _current
        else:
            return self.last

    @property
    def _current(self):
        return int(self.view.request.session.get('current_step', 0))

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
        return self.step_key(1)

    @property
    def prev(self):
        return self.step_key(-1)

    @property
    def next_is_done(self):
        return self.next == self.done_name

    @property
    def next_url(self):
        return reverse(
            self.view.request.resolver_match.view_name,
            kwargs={'step': self.current},
        )

    def finished(self, step):
        return self._goto_step_submit or step == self.done_name

    def set_from_get(self, step_url_param):
        step = step_url_param or self.current
        self.view.request.session['current_step'] = step

    def set_from_post(self):
        step = self.view.request.POST.get('wizard_current_step', self.current)
        self.view.request.session['current_step'] = step

    def advance(self):
        self.view.request.session['current_step'] = self.next

    def step_key(self, adjustment):
        key = self.current + adjustment
        if key <= 0:
            return None
        elif self.step_count > key:
            return self.view.forms[key].page_index
        elif self.step_count == key:
            return self.done_name
        else:
            return None


class StorageHelper(object):

    def __init__(self, view):
        self.view = view

    @property
    def get_form_data(self):
        self.init_form_data()
        return self.view.request.session['wizard']

    def init_form_data(self):
        self.view.request.session.setdefault('wizard', {})

    def set_form_data(self, form):
        self.init_form_data()
        self.view.request.session['wizard'][self.view.steps.current] = form.data


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

    @property
    def form(self):
        return self.get_form()

    @property
    def forms(self):
        return self.form_manager.forms

    def get_form(self):
        return self.forms[self.steps.current]

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
        self.steps.advance()
        self.storage.set_form_data(form)
        return self.render_step(**kwargs)

    def render_step(self, **kwargs):
        return HttpResponseRedirect(self.steps.next_url)

    def render_done(self, **kwargs):
        return JsonResponse(self.storage.get_form_data)
