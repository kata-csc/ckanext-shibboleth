# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

version = '0.2.1'

setup(
    name='ckanext-repoze-who-shibboleth',
    version=version,
    description="",
    long_description="""\
    """,
    classifiers=[],
    # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author=u'CSC – IT Center for Science Ltd.',
    author_email='kata-project@postit.csc.fi',
    url='https://github.com/kata-csc/ckanext-shibboleth',
    license='AGPL',
    packages=find_packages(exclude=['ez_setup', 'tests']),
    namespace_packages=['ckanext',
                        'ckanext.repoze',
                        'ckanext.repoze.who',
                        'ckanext.repoze.who.shibboleth'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    setup_requires=['nose>=1.0', 'coverage'],
    tests_require=['nose'],
    message_extractors = {
        'ckanext': [
                        ('**.py', 'python', None),#
                        ('repoze/who/shibboleth/templates/user/**.html', 'ckan', None),
                        
                        ],
    },
    entry_points="""
    [ckan.plugins]
    shibboleth=ckanext.repoze.who.shibboleth.extension:CkanShibbolethPlugin
    """,
)
