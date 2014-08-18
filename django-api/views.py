'''
Created on 15 Aug 2014

@author: tris
'''
from django.views.generic import base, edit
from django.forms.models import model_to_dict
from django.http import Http404

import django_api.schemes.basic

import logging
logger = logging.getLogger(__name__)

class APIResponseMixin(base.TemplateResponseMixin):

    api = None

    api_schemes = {'json': django_api.schemes.basic.JSONAPI,
                   'yaml': django_api.schemes.basic.YAMLAPI}

    def get_api_scheme_name(self):

        # client can explicitly request with output parameter
        if 'api' in self.request.GET:
            return self.request.GET['api']

        if 'api' in self.kwargs:
            return self.kwargs['api']

        # set via a url or subclass
        if self.api:
            return self.api

    def get_api_scheme(self, name):
        if not name in self.api_schemes:
            raise Http404("No such api: %s" % name)

        return self.api_schemes[name]()

    def get_api_data(self, context):
        '''
        Does a simple inspection of the context to handle common cases.
        Subclasses should override this method to control precisely what is returned.
        '''
        if 'object' in context:
            return model_to_dict(context['object'], exclude='id')

        if 'object_list' in context:
            return list(context['object_list'].values())

        return context

    def render_to_response(self, context):

        api = self.get_api_scheme_name()

        if not api:
            return super(APIResponseMixin, self).render_to_response(context)

        scheme = self.get_api_scheme(api)

        # all overriding by subclasses based on api
        method = getattr(self, "get_%s_api_data" % api, self.get_api_data)

        try:
            return scheme.success(method(context))
        except Exception, e:
            return scheme.failure(e)

class APIFormMixin(APIResponseMixin, edit.FormMixin):

    def get_default_api_values(self):

        # for ModelForm instances we'll preload the data with the current
        # values so the caller doesn't have to supply all the fields.
        if isinstance(self, edit.ModelFormMixin) and hasattr(self, 'object'):
            if getattr(self, 'fields', None):
                return { x: getattr(self.object, x) for x in self.fields }
            else:
                return model_to_dict(self.object)

        return {}

    def get_form_kwargs(self):
        kwargs = super(APIFormMixin, self).get_form_kwargs()

        self.api_scheme_name = self.get_api_scheme_name()

        if self.api_scheme_name:
            logger.debug("Using scheme: %s" % self.api_scheme_name)
            self.api_scheme = self.get_api_scheme(self.api_scheme_name)

            data = {}
            data.update(self.get_default_api_values())

            if not self.api_scheme.can_parse(self.request.META['CONTENT_TYPE']):
                raise Http404("Unable to parse POST body: %s" % self.request.META['CONTENT_TYPE'])
            data.update(self.api_scheme.parse_body(self.request.body))

            logger.info(data)

            kwargs['data'] = data

        return kwargs

    def form_valid(self, form):
        result = super(APIFormMixin, self).form_valid(form)
        data = {'result': "success"}
        if hasattr(self, 'api_scheme'):
            if 'location' in result:
                data['location'] = result['location']
            if hasattr(self, 'object'):
                data['id'] = self.object.pk
            return self.api_scheme.success(data)
        return result

    def form_invalid(self, form):
        result = super(APIFormMixin, self).form_invalid(form)
        if hasattr(self, 'api_scheme'):
            return self.api_scheme.failure(_form_errors(form._errors))
        return result

def _form_errors(errors, sep=', ', field_template='{0}: {1}'):
    '''
    Takes a ValidationError dict and flattens it to a single string.
    '''
    messages = []
    for x in errors:
        if x == '__all__':
            messages += errors[x]
        else:
            messages += [field_template.format(x, y) for y in errors[x] ]
    return sep.join(messages)
