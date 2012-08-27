import logging
from webob import Request, Response
from zope.interface import implements, directlyProvides
from repoze.who.interfaces import IIdentifier
from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin
from repoze.who.interfaces import IChallengeDecider
from ckan.model import User, Session, meta
from routes import url_for

log = logging.getLogger("ckanext.repoze")

SHIBBOLETH = 'shibboleth'


def make_identification_plugin(**kwargs):
    return ShibbolethIdentifierPlugin(**kwargs)

class ShibbolethBase(object):
    def is_shib_session(self, env):
        return env.get(self.session, False) and env.get('AUTH_TYPE', '') == SHIBBOLETH

class ShibbolethIdentifierPlugin(AuthTktCookiePlugin, ShibbolethBase):
    implements(IIdentifier)
    
    def __init__(self, session, mail, name, *args, **kwargs):
        self.session = session
        self.mail = mail
        self.name = name
    
    def identify(self, environ):
        user = None
        
        request = Request(environ)
        log.debug(request.path)
        
        # Logout user
        if request.path == url_for(controller='user', action='logout'):
            response = Response()
            
            for a,v in self.forget(environ,{}):
                response.headers.add(a,v)
            
            response.status = 302
            response.location = url_for(controller='user', action='logged_out')
            environ['repoze.who.application'] = response
            
            return {}
        
        # Login user, if there's shibboleth headers and path is shiblogin
        if self.is_shib_session(environ) and 'shiblogin' in request.path:
            log.debug("Trying to authenticate with shibboleth")
            log.debug('environ AUTH TYPE: %s', environ.get('AUTH_TYPE', 'None'))
            log.debug('environ Shib-Session-ID: %s', environ.get(self.session, 'None'))
            log.debug('environ mail: %s', environ.get(self.mail, 'None'))
            log.debug('environ cn: %s', environ.get(self.name, 'None'))
            
            user = self._get_or_create_user(environ)

            if not user:
                log.debug('User is None')
                return None
            
            response = Response()
            response.status = 302
            response.location = url_for(controller='user', action='dashboard')
            environ['repoze.who.application'] = response
            
            return {'repoze.who.plugins.openid.userid':user.openid,
                    'login':user.email,
                    'password':'',
                    'email':user.email,
                    'fullname':user.email}
            
        return None
    
    def _get_or_create_user(self, env):
        #WSGI Variables
        #Shib-Application-ID            'default'
        #Shib-Authentication-Instant    '2012-08-13T12:04:22.492Z'
        #Shib-Authentication-Method     'urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport'
        #Shib-AuthnContext-Class        'urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport'
        #Shib-Identity-Provider         'https://idp.example.com/idp/shibboleth'
        #Shib-Session-ID                '_7ec5a681e6dbae627c1cefcc7cb4d56a'
        #Shib-Session-Index             '39dafd8477850f5e0b968e3561570197f2109948c1d374a7a2b4c9a7adbf8628'
        #cn                             'My Other Self'
        #givenName                      'My Other Self'
        #mail                           'myother@self.com'
        
        email = env.get(self.mail, None)
        fullname = env.get(self.name, None)
        
        if not email or not fullname:
            log.debug('Environ does not contain mail or cn attributes, user not loaded.')
            return None
    
        user = meta.Session.query(User).autoflush(False) \
                    .filter_by(openid=email).first()
                    
        if user is None:
            log.debug('User does not exists, creating new one.')
        
            import re
            username = re.sub('[.@]', '_', email)
        
            user = User(name     = username,
                        fullname = fullname,
                        email    = email,
                        openid   = email)
            
            Session.add(user)
            Session.commit()
            Session.remove()

            log.debug("Created new user %s" % fullname)
        
        return user

    def _get_rememberer(self, environ):
        plugins = environ.get('repoze.who.plugins', {})
        return plugins.get('auth_tkt')

    def remember(self, environ, identity):
        rememberer = self._get_rememberer(environ)
        return rememberer and rememberer.remember(environ, identity)

    def forget(self, environ, identity):
        rememberer = self._get_rememberer(environ)
        return rememberer and rememberer.forget(environ, identity)

