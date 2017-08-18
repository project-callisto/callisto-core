from django.core.urlresolvers import reverse_lazy
from django.http.response import HttpResponseRedirect
from django.views import generic as views

from . import managers, view_helpers


class NewWizardView(views.base.RedirectView):
    url = reverse_lazy(
        'wizard_update',
        kwargs={'step': 0},
    )


class WizardViewTemplateHelpers(object):

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

    @property
    def wizard_form_pk_field(self):
        # TODO: smell this being the only storage attribute accessed in view
        return self.storage.form_pk_field


class WizardView(
    WizardViewTemplateHelpers,
    views.edit.FormView,
):
    site_id = None
    url_name = None
    template_name = 'wizard_builder/wizard_form.html'
    done_template_name = 'wizard_builder/review.html'
    steps_helper = view_helpers.StepsHelper
    storage_helper = view_helpers.StorageHelper
    form_manager = managers.FormManager

    @property
    def steps(self):
        return self.steps_helper(self)

    @property
    def storage(self):
        return self.storage_helper(self)

    def get_forms(self):
        return self.form_manager.get_forms(self)

    def get_form(self):
        if isinstance(self.steps.current, int):
            return self.forms[self.steps.current]
        else:
            return None

    def dispatch(self, request, step=None, *args, **kwargs):
        self.curent_step = self.steps.parse_step(step)
        self.forms = self.get_forms()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.steps.set_from_post()
        output = super().post(request, *args, **kwargs)
        return output

    def form_valid(self, form):
        self.storage.update()
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
