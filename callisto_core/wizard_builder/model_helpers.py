class ProxyQuestion:

    def __init__(self, *args, **kwargs):
        self._meta.get_field('type').default = self.proxy_name
        super().__init__(*args, **kwargs)

    class Meta:
        proxy = True
