from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect, JsonResponse
from django.views.generic.edit import FormView

from .managers import FormManager


class StepsHelper(object):
    done_name = 'done'

    def __init__(self, view):
        self.view = view

    @property
    def all(self):
        return self.view.manager.forms

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
    def _goto_step_back(self):
        return self._goto_step('Back')

    @property
    def _goto_step_next(self):
        return self._goto_step('Next')

    @property
    def _goto_step_submit(self):
        return self._goto_step('Submit')

    @property
    def first(self):
        return 0

    @property
    def last(self):
        return self.all[-1].manager_index

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
    def last_url(self):
        return self.url(self.last)

    @property
    def done_url(self):
        return self.url(self.done_name)

    def _goto_step(self, step_type):
        post = self.view.request.POST
        return post.get('wizard_goto_step', None) == step_type

    def url(self, step):
        return reverse(
            self.view.request.resolver_match.view_name,
            kwargs={'step': step},
        )

    def overflowed(self, step):
        return int(step) > int(self.last)

    def finished(self, step):
        return self._goto_step_submit or step == self.done_name

    def set_from_get(self, step_url_param):
        step = step_url_param or self.current
        self.view.request.session['current_step'] = step

    def set_from_post(self):
        step = self.view.request.POST.get('wizard_current_step', self.current)
        if self._goto_step_back:
            step = self.adjust_step(-1)
        if self._goto_step_next:
            step = self.adjust_step(1)
        self.view.request.session['current_step'] = step

    def adjust_step(self, adjustment):
        # TODO: tests as spec
        key = self.current + adjustment
        if key < self.first:
            return None
        if key == self.first:
            return self.first
        elif self.step_count > key:
            return self.view.manager.forms[key].manager_index
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
            self.view.request.session[self.key(form.pk)]
            for form in self.view.manager.forms
        ]}

    @property
    def post_form_pk(self):
        return self.view.form_pk(self.view.request.POST[
            self.view.form_pk_field])

    @property
    def post_data(self):
        data = self._data_from_key(self.post_form_pk)
        data.update(self.view.request.POST)
        return data

    def set_form_data(self):
        self.view.request.session[self.post_form_pk] = self.post_data

    def data_from_pk(self, pk):
        key = self.view.form_pk(pk)
        return self._data_from_key(key)

    def _data_from_key(self, key):
        return self.view.request.session.get(key, {})


class WizardView(FormView):
    site_id = None
    url_name = None
    template_name = 'wizard_builder/wizard_form.html'
    form_pk_field = 'form_pk'

    @property
    def steps(self):
        return StepsHelper(self)

    @property
    def storage(self):
        return StorageHelper(self)

    @property
    def manager(self):
        return FormManager(self)

    def form_pk(self, pk):
        return '{}_{}'.format(self.form_pk_field, pk)

    def get_form(self):
        return self.manager.forms[self.steps.current]

    def dispatch(self, request, step=None, *args, **kwargs):
        self.steps.set_from_get(step)
        if self.steps.finished(step):
            return self.render_done(**kwargs)
        elif self.steps.overflowed(step):
            return self.render_last(**kwargs)
        else:
            return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.steps.set_from_post()
        self.storage.set_form_data()
        return self.render_current()

    def render_done(self, **kwargs):
        if self.steps.current_is_done:
            # TODO: a review screen template
            return JsonResponse(self.storage.get_form_data)
        else:
            return HttpResponseRedirect(self.steps.done_url)

    def render_last(self, **kwargs):
        return HttpResponseRedirect(self.steps.last_url)

    def render_current(self, **kwargs):
        return HttpResponseRedirect(self.steps.current_url)
