from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IGenshiStreamFilter
from genshi.filters.transform import Transformer
from genshi.input import HTML

from ckanext.repoze.who.shibboleth.plugin import SHIBBOLETH

shib_login = """<form action="/user/shiblogin" method="GET">
<input type="hidden" name="%s" value="1" />
<input type="submit" name="" value="login using shibboleth"  />
</form>
""" % SHIBBOLETH


class CkanShibbolethPlugin(SingletonPlugin):
    implements(IGenshiStreamFilter)

    def filter(self, stream):
        from pylons import request
        routes = request.environ.get('pylons.routes_dict')
        if routes.get('controller') == 'user' and routes.get('action') == 'login':
            stream = stream | Transformer('//div[@id="content"]').prepend(HTML(shib_login))
        return stream
