import logging

from zope.interface import implements
from repoze.who.interfaces import IAuthenticator

from ckan.model import User, Session

log = logging.getLogger(__name__)

class ShibbolethAuthenticator(object):
    implements(IAuthenticator)

    def authenticate(self, environ, identity):
        if 'repoze.who.plugins.openid.userid' in identity:
            openid = identity.get('repoze.who.plugins.openid.userid')
            user = User.by_openid(openid)
            if user is None:
                return None
            else:
                return user.name
        return None
