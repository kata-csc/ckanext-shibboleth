# -*- coding: utf8 -*-

import logging

from repoze.who.interfaces import IIdentifier
from routes import url_for
from webob import Request, Response
from zope.interface import implements

import ckan.model as model
import ckanext.kata.model as kmodel
import ckanext.shibboleth.utils as utils

log = logging.getLogger("ckanext.repoze.who.shibboleth")

SHIBBOLETH = 'shibboleth'


def make_identification_plugin(**kwargs):
    return ShibbolethIdentifierPlugin(**kwargs)


class ShibbolethBase(object):
    def is_shib_session(self, env):
        return env.get(self.session, False) and env.get('AUTH_TYPE',
                                                        '') == SHIBBOLETH


class ShibbolethIdentifierPlugin(ShibbolethBase):
    implements(IIdentifier)

    def __init__(self, session, eppn, mail, fullname, **kwargs):
        '''
        Parameters here contain just names of the environment attributes defined
        in who.ini, not their values:
        @param session: 'Shib-Session-ID'
        @param eppn: 'eppn'
        @param organization: 'schacHomeOrganization'
        etc.
        '''
        self.session = session
        self.eppn = eppn
        self.mail = mail
        self.fullname = fullname
        self.extra_keys = {}
        for field in utils.EXTRAS:
            self.extra_keys[field] = kwargs.get(field, None)

        controller = 'ckanext.repoze.who.shibboleth.controller:ShibbolethController'
        self.login_url = url_for(controller=controller, action='shiblogin')
        self.logout_url = url_for(controller='user', action='logout')

    def identify(self, environ):
        request = Request(environ)
        # log.debug('Request path: %s' % request.path)
        # log.debug(pprint.pformat(request))
        # log.debug('environ: {env}'.format(env=pprint.pformat(environ)))

        # Logout user
        if request.path == self.logout_url:
            response = Response()

            for a, v in self.forget(environ, {}):
                response.headers.add(a, v)

            response.status = 302
            url = url_for(controller='user', action='logged_out')
            locale = environ.get('CKAN_LANG', None)
            default_locale = environ.get('CKAN_LANG_IS_DEFAULT', True)
            if not default_locale and locale:
                url = "/%s%s" % (locale, url)

            response.location = url
            environ['repoze.who.application'] = response

            return {}

        # Login user, if there's shibboleth headers and path is shiblogin
        if self.is_shib_session(environ) and request.path == self.login_url:
        # log.debug("Trying to authenticate with shibboleth")
        # log.debug('environ AUTH TYPE: %s', environ.get('AUTH_TYPE', 'None'))
        # log.debug('environ Shib-Session-ID: %s', environ.get(self.session, 'None'))
        # log.debug('environ mail: %s', environ.get(self.mail, 'None'))
        # log.debug('environ cn: %s', environ.get(self.name, 'None'))

            user = self._get_or_create_user(environ)

            if not user:
            # log.debug('User is None')
                return {}

            # TODO: Fix flash message later, maybe some other place
            #h.flash_success(
            #    _('Profile updated or restored from {idp}.').format(
            #        idp=environ.get('Shib-Identity-Provider',
            #                        'IdP not aquired')))
            response = Response()
            response.status = 302
            response.location = url_for(controller='user', action='read')
            environ['repoze.who.application'] = response

            return {'repoze.who.plugins.openid.userid': user.openid,
                    'login': user.email,
                    'password': '',
                    'email': user.email,
                    'fullname': user.email}

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
        extras = {}
        for field in utils.EXTRAS:
            extras[field] = env.get(self.extra_keys[field], None)

        if not eppn or not fullname:
            log.debug(
                'Environ does not contain eppn or cn attributes, user not loaded.')
            return None

        user = model.Session.query(model.User).autoflush(False) \
            .filter_by(openid=eppn).first()

        # Check if user information from shibboleth has changed
        if user:
            old_extras = utils.fetch_user_extra(user.id)
            if (user.fullname != fullname or user.email != email):
                log.debug('User attributes modified, updating.')
                user.fullname = fullname
                user.email = email
            for key, val in old_extras.iteritems():
                if extras[key] != val:
                    log.debug('User extra attribute {att} modified, updating.'
                    .format(att=key))
                    extra = kmodel.UserExtra.by_userid_key(user.id, key=key)
                    extra.value = extras[key]
            # Check for new attributes
            new_extra_keys = set(extras.keys()) - set(old_extras.keys())
            if new_extra_keys:
                log.debug('New user extra attribute {att} found, updating.'
                          .format(att=key))
                for key in new_extra_keys:
                    extra = kmodel.UserExtra(user_id=user.id, key=key,
                                             value=extras[key])
                    model.Session.add(extra)

        else:  # user is None:
            log.debug('User does not exists, creating new one.')

            basename = unicode(fullname, errors='ignore').lower().replace(' ',
                                                                          '_')
            username = basename
            suffix = 0
            while not model.User.check_name_available(username):
                suffix += 1
                username = basename + str(suffix)

            user = model.User(name=username,
                              fullname=fullname,
                              email=email,
                              openid=eppn)

            model.Session.add(user)
            # TODO: Instead this extra table mess up, use Mapping Class ...
            # ... Inheritance?:
            # http://stackoverflow.com/questions/1337095/sqlalchemy-inheritance
            # This might be unfeasible if requires tweaking CKAN user model.
            # We need to get the user id so flush and user is written to db.
            model.Session.flush()
            userid = user.id
            #new
            for key, value in extras.iteritems():
                if value:
                    extra = kmodel.UserExtra(user_id=userid,
                                             key=key,
                                             value=value)
                    model.Session.add(extra)
            log.debug('Created new user {usr}'.format(usr=fullname))

        model.Session.commit()
        model.Session.remove()
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

