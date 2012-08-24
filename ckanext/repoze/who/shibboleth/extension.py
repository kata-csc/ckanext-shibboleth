from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IGenshiStreamFilter
from genshi.filters.transform import Transformer
from genshi.input import HTML

shibboleth_login =\
"""
<li class=""><a href="%s">Shibboleth login</a></li>
""" % '/user/shiblogin'


class CkanShibbolethPlugin(SingletonPlugin):
    implements(IGenshiStreamFilter)

    def filter(self, stream):
        from pylons import request
        routes = request.environ.get('pylons.routes_dict')
        if routes.get('controller') == 'user' and routes.get('action') == 'login':
            stream = stream | Transformer('//ul[@class="nav nav-pills"]').append(HTML(shibboleth_login))
        return stream
