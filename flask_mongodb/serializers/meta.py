from wtforms.meta import DefaultMeta


class SerializerMeta(DefaultMeta):
    def render_field(self, field, render_kw):
        """
        render_field allows customization of how widget rendering is done.

        The default implementation calls ``field.widget(field, **render_kw)``
        """

        super().render_field(field, render_kw)

    # -- CSRF

    _csrf = False
    _csrf_field_name = "serializer_csrf"
    _csrf_secret = None
    _csrf_context = None
    _csrf_class = None

    def build_csrf(self, form):
        """
        Build a CSRF implementation. This is called once per form instance.

        The default implementation builds the class referenced to by
        :attr:`csrf_class` with zero arguments. If `csrf_class` is ``None``,
        will instead use the default implementation
        :class:`wtforms.csrf.session.SessionCSRF`.

        :param form: The form.
        :return: A CSRF implementation.
        """
        if self.csrf_class is not None:
            return self.csrf_class()

        from wtforms.csrf.session import SessionCSRF

        return SessionCSRF()
    
    @property
    def csrf(self):
        return self._csrf
    
    @property
    def csrf_field_name(self):
        return self._csrf_field_name
    
    @property
    def csrf_secret(self):
        return self._csrf_secret
    
    @property
    def csrf_context(self):
        return self._csrf_context
    
    @property
    def csrf_class(self):
        return self._csrf_class