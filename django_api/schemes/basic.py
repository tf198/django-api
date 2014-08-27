'''
Created on 15 Aug 2014

@author: tris
'''
import json
from django.http import HttpResponse

import logging
logger = logging.getLogger(__name__)

class BasicAPI(object):

    content_types = ()

    def can_parse(self, content_type):
        return content_type in self.content_types

    def get_content_type(self):
        return self.content_types[0]

    def encode(self, data):
        raise RuntimeError("Need to implement encode()")

    def success(self, result):
        return HttpResponse(self.encode(result), content_type=self.get_content_type())

    def failure(self, e):
        data = {'errors': {'description': str(e)}}
        return HttpResponse(self.encode(data), content_type=self.get_content_type(), status=400)

class JSONMixin(object):

    content_types = ('application/json', 'text/json')

    def parse_body(self, body):
        return json.loads(body)

    def encode(self, data):
        return json.dumps(data, indent=1)

class YAMLMixin(object):

    content_types = ('application/yaml', 'text/yaml')

    def parse_body(self, body):
        import yaml
        return yaml.safe_load(body)

    def encode(self, data):
        import yaml
        return yaml.safe_dump(data)

class JSONAPI(JSONMixin, BasicAPI):
    pass

class YAMLAPI(YAMLMixin, BasicAPI):
    pass

