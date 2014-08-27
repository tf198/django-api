from django.forms.models import model_to_dict

def _map_fields(data, keymap):
    if not keymap: return data

    return { keymap.get(x, x): data[x] for x in data }

def _map_items(data, keymap):
    if not keymap: return data

    return [ keymap.get(x, x) for x in data ]

def get_dict_fields(d, fields=None, exclude=None, keymap=None):

    if exclude:
        fields = [ x for x in d.keys() if not x in exclude ]

    if fields is None:
        return d

    return _map_fields({ x: d[x] for x in fields }, keymap)

def dict_selector(fields=None, exclude=None, keymap=None):

    def f(view, data):
        return get_dict_fields(data, fields, exclude, keymap)
    return f

def get_model_fields(obj, fields=None, exclude=None, keymap=None):
    # d = model_to_dict(obj, fields=fields, exclude=exclude)

    if fields == None:
        fields = [ x.name for x in obj._meta.concrete_fields ]

    if exclude is None:
        exclude = []

    d = { x: getattr(obj, x) for x in fields if not x in exclude }

    return _map_fields(d, keymap)

def model_selector(fields=None, exclude=None, keymap=None, accessor='object'):

    def f(view, data):
        return get_model_fields(data[accessor], fields, exclude, keymap)
    return f

def get_queryset_fields(qs, fields=None, exclude=None, keymap=None, headings=False):

    l_fields = fields or []

    if exclude:
        l_fields = [ x for x in qs.model._meta.get_all_field_names() if not x in exclude ]

    if headings:
        result = [_map_items(l_fields)] + list(qs.values_list(*l_fields))
    else:
        result = list(qs.values(*l_fields))
        if keymap:
            result = [ _map_fields(x, keymap) for x in result ]

    return result

def queryset_selector(fields=None, exclude=None, keymap=None, accessor='object_list', headings=False):

    def f(view, data):
        return get_queryset_fields(data[accessor], fields, exclude, keymap, headings)
    return f
