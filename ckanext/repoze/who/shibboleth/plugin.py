import logging

from zope.interface import implements, directlyProvides
from repoze.who.interfaces import IIdentifier
from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin
from repoze.who.interfaces import IChallengeDecider
from ckan.model import User, Session, meta

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
        log.info("Trying to authenticate with shibboleth")
        log.info('environ AUTH TYPE: %s', environ.get('AUTH_TYPE', 'None'))
        log.info('environ Shib-Session-ID: %s', environ.get(self.session, 'None'))
        log.info('environ mail: %s', environ.get(self.mail, 'None'))
        log.info('environ cn: %s', environ.get(self.name, 'None'))
        
        user = None

        if self.is_shib_session(environ):
            logging.warning("Found shibboleth session")
            user = self._get_or_create_user(environ)

        if not user:
            return None
        
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
            log.info('Environ does not contain mail or cn attributes, user not loaded.')
            return None
    
        user = meta.Session.query(User).autoflush(False) \
                    .filter_by(openid=email).first()
                    
        if user is None:
            log.info('User does not exists, creating new one.')
        
            import re
            username = re.sub('[.@]', '_', email)
        
            user = User(name     = username,
                        fullname = fullname,
                        email    = email,
                        openid   = email)
            
            Session.add(user)
            Session.commit()
            Session.remove()

            log.info("Created new user %s" % fullname)
        
        return user

    def _get_rememberer(self, environ):
        plugins = environ.get('repoze.who.plugins', {})
        return plugins.get('auth_tkt')

    def remember(self, environ, identity):
        rememberer = self._get_rememberer(environ)
        logging.info("Remembering %r" % identity)
        return rememberer and rememberer.remember(environ, identity)

    def forget(self, environ, identity):
        rememberer = self._get_rememberer(environ)
        logging.info("Forgetting %r" % identity)
        return rememberer and rememberer.forget(environ, identity)

def shibboleth_challenge_decider(environ, status, headers):
    if status.startswith('401 '):
        return True
    elif 'ckan.who.shibboleth.challenge' in environ:
        return True
    elif 'repoze.whoplugins.openid.openid' in environ:
        return True

    return False

directlyProvides(shibboleth_challenge_decider, IChallengeDecider)