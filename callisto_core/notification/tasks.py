from celeryconfig.basetask import CoreBaseTask


@shared_task(name='send_email', bind=True)
def send_email(email_data, email_attachments=None):
    mailgun_post_route = f'https://api.mailgun.net/v3/{settings.APP_URL}/messages'
    request_params = {
        'auth': ('api', settings.MAILGUN_API_KEY),
        'data': {
            'from': f'"Callisto" <noreply@{settings.APP_URL}>',
            **email_data,
        },
        **email_attachments,
    }
    response = requests.post(self.mailgun_post_route, request_params)
    return response
