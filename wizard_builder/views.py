from django.core.urlresolvers import reverse_lazy
from django.http.response import HttpResponseRedirect
from django.views import generic as views

from . import managers, view_helpers


class NewWizardView(views.base.RedirectView):
    url = reverse_lazy(
        'wizard_update',
        kwargs={'step': 0},
    )


class WizardView(views.edit.FormView):
    site_id = None
    url_name = None
    template_name = 'wizard_builder/wizard_form.html'
    done_template_name = 'wizard_builder/review.html'
    form_pk_field = 'form_pk'
    steps_helper = view_helpers.StepsHelper
    storage_helper = view_helpers.StorageHelper
    form_manager = managers.FormManager

    @property
    def steps(self):
        return self.steps_helper(self)

    @property
    def storage(self):
        return self.storage_helper(self)

    @property
    def manager(self):
        return self.form_manager(self)

    def form_pk(self, pk):
        return '{}_{}'.format(self.form_pk_field, pk)

    def get_form(self):
        return self.manager.forms[self.steps.current]

    def dispatch(self, request, step=None, *args, **kwargs):
        self.steps.set_from_get(step)
        if self.steps.finished(step):
            return self.dispatch_done(request, step, **kwargs)
        elif self.steps.overflowed(step):
            return self.render_last(**kwargs)
        else:
            return super().dispatch(request, *args, **kwargs)

    def dispatch_done(self, request, step=None, *args, **kwargs):
        if self.steps.current_is_done:
            return self.render_finished(**kwargs)
        else:
            return self.render_done(**kwargs)

    def post(self, request, *args, **kwargs):
        self.steps.set_from_post()
        self.storage.set_form_data()
        return self.render_current()

    def get_context_data(self, **kwargs):
        if self.steps.current_is_done:
            self.template_name = self.done_template_name
            kwargs['form'] = None
            kwargs['form_data'] = self.storage.cleaned_form_data
            return super().get_context_data(**kwargs)
        else:
            return super().get_context_data(**kwargs)

    def render_done(self, **kwargs):
        return HttpResponseRedirect(self.steps.done_url)

    def render_finished(self, **kwargs):
        return self.render_to_response(self.get_context_data())

    def render_last(self, **kwargs):
        return HttpResponseRedirect(self.steps.last_url)

    def render_current(self, **kwargs):
        return HttpResponseRedirect(self.steps.current_url)
