from ..delivery import view_partials as delivery_view_partials
from ..utils import api


class BaseReportingView(
    delivery_view_partials.ReportUpdateView,
):

    def form_valid(self, form):
        output = super().form_valid(form)
        if form.cleaned_data.get('email_confirmation') == "True":
            api.NotificationApi.send_user_notification(
                form,
                self.email_confirmation_name,
                self.site_id,
            )
        return output
