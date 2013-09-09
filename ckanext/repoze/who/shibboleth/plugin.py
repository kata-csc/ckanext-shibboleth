# -*- coding: utf8 -*-

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
    
    def __init__(self, session, eppn, mail, fullname, firstname, surname,
                 organization, mobile, telephone, *args, **kwargs):
        self.session = session
        self.eppn = eppn
        self.mail = mail
        self.fullname = fullname
        self.firstname = firstname
        self.surname = surname
        self.organization = organization
        self.mobile = mobile
        self.telephone = telephone
        
        controller = 'ckanext.repoze.who.shibboleth.controller:ShibbolethController'
        self.login_url = url_for(controller=controller, action='shiblogin')
        self.logout_url = url_for(controller='user', action='logout')
    
    def identify(self, environ):
        user = {}
        request = Request(environ)
        
#        log.debug('Request path: %s' % request.path)
#        log.debug(request)
#        log.debug(environ)

        # Logout user
        if request.path == self.logout_url:
            response = Response()
            
            for a,v in self.forget(environ,{}):
                response.headers.add(a,v)
            
            response.status = 302
            response.location = url_for(controller='user', action='logged_out')
            environ['repoze.who.application'] = response
            
            return {}
        
        # Login user, if there's shibboleth headers and path is shiblogin
        if self.is_shib_session(environ) and request.path == self.login_url:
#            log.debug("Trying to authenticate with shibboleth")
#            log.debug('environ AUTH TYPE: %s', environ.get('AUTH_TYPE', 'None'))
#            log.debug('environ Shib-Session-ID: %s', environ.get(self.session, 'None'))
#            log.debug('environ mail: %s', environ.get(self.mail, 'None'))
#            log.debug('environ cn: %s', environ.get(self.name, 'None'))
            
            user = self._get_or_create_user(environ)

            if not user:
#                log.debug('User is None')
                return {}
            
            response = Response()
            response.status = 302
            response.location = url_for(controller='user', action='read')
            environ['repoze.who.application'] = response
            
            return {'repoze.who.plugins.openid.userid':user.openid,
                    'login':user.email,
                    'password':'',
                    'email':user.email,
                    'fullname':user.email}
            
        return {}
    
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

        eppn = env.get(self.eppn, None)
        fullname = env.get(self.fullname, None)
        email = env.get(self.mail, None)

        if not eppn or not fullname:
            log.debug('Environ does not contain eppn or cn attributes, user not loaded.')
            return None
    
        user = meta.Session.query(User).autoflush(False) \
                    .filter_by(openid=eppn).first()
                    
        if user is None:
            log.debug('User does not exists, creating new one.')

            username = unicode(fullname, errors='ignore').lower().replace(' ', '_')
            suffix = 0
            while not User.check_name_available(username):
                 suffix += 1
                 username =  fullname + suffix

            user = User(name     = username,
                        fullname = fullname,
                        email    = email,
                        openid   = eppn)
            
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

