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
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        output = super().post(request, *args, **kwargs)
        self.steps.set_from_post()
        self.storage.update()
        return output

    def form_valid(self, form):
        if self.steps.finished(self.steps.current):
            return self.render_form_done()
        elif self.steps.overflowed(self.steps.current):
            return self.render_last()
        else:
            return self.render_current()

    def get_context_data(self, **kwargs):
        if self.steps.current_is_done:
            self.template_name = self.done_template_name
            kwargs['form'] = None
            kwargs['form_data'] = self.storage.cleaned_form_data
            return super().get_context_data(**kwargs)
        else:
            return super().get_context_data(**kwargs)

    def render_form_done(self):
        if self.steps.current_is_done:
            return self.render_finished()
        else:
            return self.render_done()

    def render_done(self):
        return HttpResponseRedirect(self.steps.done_url)

    def render_finished(self):
        return self.render_to_response(self.get_context_data())

    def render_last(self):
        return HttpResponseRedirect(self.steps.last_url)

    def render_current(self):
        return HttpResponseRedirect(self.steps.current_url)
