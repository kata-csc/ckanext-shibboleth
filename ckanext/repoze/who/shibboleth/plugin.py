# -*- coding: utf8 -*-
'''
Repoze.who plugin for ckanext-shibboleth
'''

import logging

from repoze.who.interfaces import IIdentifier, IChallenger
from routes import url_for
from webob import Request, Response
from zope.interface import implements
import urllib

import ckan.model as model
import ckanext.kata.model as kmodel
import ckanext.shibboleth.utils as utils

from urlparse import urlparse, urlunparse, parse_qs


log = logging.getLogger("ckanext.repoze.who.shibboleth")

SHIBBOLETH = 'shibboleth'


def make_identification_plugin(**kwargs):
    return ShibbolethIdentifierPlugin(**kwargs)


class ShibbolethBase(object):
    def is_shib_session(self, env):
        return env.get(self.session, False) and env.get('AUTH_TYPE',
                                                        '') == SHIBBOLETH


class ShibbolethIdentifierPlugin(ShibbolethBase):
    implements(IChallenger, IIdentifier)

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
        self.login_form_url = url_for(controller='user', action='login')
        self.logout_url = url_for(controller='user', action='logout')

    def challenge(self, environ, status, app_headers, forget_headers):
        '''
        repoze.who.interfaces.IChallenger.challenge.

        "Conditionally initiate a challenge to the user to provide credentials."

        "Examine the values passed in and return a WSGI application which causes a
        challenge to be performed.  Return None to forego performing a challenge."

        :param environ:  the WSGI environment
        :param status:  status written into start_response by the downstream application.
        :param app_headers:  the headers list written into start_response by the downstream application.
        :param forget_headers:
        :return:
        '''
        request = Request(environ)

        locale_default = environ.get('CKAN_LANG_IS_DEFAULT', True)
        locale = environ.get('CKAN_LANG', None)

        parsed_url = list(urlparse(request.url))
        parsed_url[0] = parsed_url[1] = ''
        requested_url = urlunparse(parsed_url)

        if not locale_default and locale and not requested_url.startswith('/%s/' % locale):
            requested_url = "/%s%s" % (locale, requested_url)

        url = self.login_form_url + "?%s=%s" % ("came_from", requested_url)

        if not locale_default and locale:
            url = "/%s%s" % (locale, url)

        response = Response()
        response.status = 302
        response.location = url

        log.info("Shibboleth response (challenge): %s (%s)" % (response, response.location))
        return response

    def identify(self, environ):
        """
        repoze.who.interfaces.IIdentifier.identify.

        "Extract credentials from the WSGI environment and turn them into an identity."

        This is called (twice) for every page load.

        :param environ:  the WSGI environment.
        :return:
        """
        request = Request(environ)

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

            log.debug("Shibboleth user logout successful.")
            return {}

        # Login user
        if self.is_shib_session(environ) and request.path == self.login_url:

            user = self._get_or_create_user(environ)
            if not user:
                return {}

            # TODO: Fix flash message later, maybe some other place
            #h.flash_success(
            #    _('Profile updated or restored from {idp}.').format(
            #        idp=environ.get('Shib-Identity-Provider',
            #                        'IdP not aquired')))
            response = Response()
            response.status = 302

            url = request.params.get('came_from', None)
            if not url:
                url = url_for(controller='package', action='search')
                locale = environ.get('CKAN_LANG', None)
                default_locale = environ.get('CKAN_LANG_IS_DEFAULT', True)
                if not default_locale and locale:
                    url = "/%s%s" % (locale, url)

            response.location = urllib.unquote(url).decode('utf8')
            environ['repoze.who.application'] = response

            log.info("Shibboleth login successful: %r (%s)" % (user, response.location))

            return {'repoze.who.plugins.openid.userid': user.openid,
                    'login': user.email,
                    'password': '',
                    'email': user.email,
                    'fullname': user.email}

        # User not logging in or logging out, return empty dict
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
            log.debug('Not enough information received for user: {eppn}, {name}, {mail}, {extras}'.
                      format(eppn=eppn, name=fullname, mail=email, extras=extras))
            return None

        log.info("Login attempt for user: %s" % (eppn,))

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
                if extras.get(key) and extras[key] != val:
                    log.debug('User extra attribute {att} modified, updating '
                              'from Shibboleth.'.format(att=key))
                    extra = kmodel.UserExtra.by_userid_key(user.id, key=key)
                    extra.value = extras[key]
            # Check for new attributes
            new_extra_keys = set(extras.keys()) - set(old_extras.keys())
            if new_extra_keys:
                for key in new_extra_keys:
                    log.debug('New user extra attribute {att} found, updating.'.format(att=key))
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
        log.debug('Using repoze.who plugin %s  (Total amount of plugins is %s)' %
                  (plugins.get('auth_tkt'), len(plugins)))
        return plugins.get('auth_tkt')

    def remember(self, environ, identity):
        '''
        Return a sequence of response headers which suffice to remember the given identity.

        :param environ:
        :param identity:
        :return:
        '''
        rememberer = self._get_rememberer(environ)
        return rememberer and rememberer.remember(environ, identity)

    def forget(self, environ, identity):
        '''
        Return a sequence of response headers which suffice to destroy any credentials used to establish an identity.

        :param environ:
        :param identity:
        :return:
        '''
        rememberer = self._get_rememberer(environ)
        return rememberer and rememberer.forget(environ, identity)
