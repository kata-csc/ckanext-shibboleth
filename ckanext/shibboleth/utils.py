#import logging

import ckan.lib.navl.validators as v
import ckan.lib.dictization as d
import ckanext.kata.model as km
import ckanext.kata.validators as kv

EXTRAS = ['firstname',
          'surname',
          'organization',
          'mobile',
          'telephone']

#log = logging.getLogger(__name__)

def fetch_user_extra(userid):
    '''
    Return extra profile information.
    More elegant might be to access extra rows through user table foreign key
    reference. Somehow.
    '''
    extra_dict = {}
    for extra in km.UserExtra.by_userid(userid):
        key = extra.as_dict()['key']
        value = extra.as_dict()['value']
        extra_dict.update({key:value})
    return extra_dict

def shibboleth_user_edit_form_schema(schema):
    '''
    Add more fields to schema for validation.

    @param schema: current schema
    @return: augmented schema
    '''
    schema['organization'] = [v.ignore_missing, unicode]
    schema['mobile'] = [v.ignore_missing, kv.validate_phonenum]
    schema['telephone'] = [v.ignore_missing, kv.validate_phonenum]
    return schema

def user_extra_save(user_dict, context):
    '''
    Save user profile extra information to database.
    Modified from ckan/lib/dictization/model_save.py:445 (user_dict_save).
    @param user_dict: dict containing user and extra information
    @param context:
    @return: list of saved model objects
    '''
    user = context.get('user_obj')
    user_extras = []

    UserExtra = km.UserExtra
    if user:
        user_dict['id'] = user.id
        for field in EXTRAS:
            if user_dict.has_key(field):
                extra_row = {}
                extra_row['key'] = field
                extra_row['value'] = user_dict[field]
                user_extra = km.UserExtra.by_userid_key(user.id, field)
                if user_extra:
                    extra_row['id'] = user_extra.id
                user_extras.append(d.table_dict_save(extra_row, UserExtra, context))

    return user_extras


