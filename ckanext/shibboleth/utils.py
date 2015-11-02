import ckan.lib.navl.validators as validators
import ckan.lib.dictization as dictization
import ckanext.kata.model as kmodel
import ckanext.kata.validators as kvalidators

EXTRAS = ['firstname',
          'surname',
          'organization',
          'mobile',
          'telephone']


def fetch_user_extra(userid):
    '''
    Return extra profile information.
    More elegant might be to access extra rows through user table foreign key
    reference. Somehow.
    '''
    extra_dict = {}
    for extra in kmodel.UserExtra.by_userid(userid):
        key = extra.as_dict()['key']
        value = extra.as_dict()['value']
        extra_dict.update({key: value})
    return extra_dict


def shibboleth_user_edit_form_schema(schema):
    '''
    Add more fields to schema for validation.

    @param schema: current schema
    @return: augmented schema
    '''
    schema['organization'] = [validators.ignore_missing, unicode]
    schema['mobile'] = [validators.ignore_missing,
                        kvalidators.validate_phonenum]
    schema['telephone'] = [validators.ignore_missing,
                           kvalidators.validate_phonenum]
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

    UserExtra = kmodel.UserExtra
    if user:
        user_dict['id'] = user.id
        for field in EXTRAS:
            if user_dict.has_key(field):
                extra_row = {}
                extra_row['key'] = field
                extra_row['value'] = user_dict[field]
                user_extra = kmodel.UserExtra.by_userid_key(user.id, field)
                if user_extra:
                    extra_row['id'] = user_extra.id
                user_extras.append(
                    dictization.table_dict_save(extra_row, UserExtra, context))

    return user_extras
