'''
Overwrite actions for shibboleth to handle extra profile information.
Modifications commented with line: # Added in ckanext-shibboleth
'''
import logging

import ckan.logic as logic
import ckan.logic.action.get as get
import ckan.lib.dictization as dictization
import ckan.lib.navl.dictization_functions
import utils

log = logging.getLogger(__name__)

# Define some shortcuts
# Ensure they are module-private so that they don't get loaded as available
# actions in the action API.
_check_access = logic.check_access
_get_action = logic.get_action
_get_or_bust = logic.get_or_bust
_validate = ckan.lib.navl.dictization_functions.validate
NotFound = logic.NotFound
ValidationError = logic.ValidationError


def user_show(context, data_dict):
    '''
    Return a user account and extra profile info.

    Minor rewrite to add additional user profile information (acquired eg. from
    shibboleth) from the user_extra table to the c.user_dict for templates.
    NOTE: 'revision_show' method still references to default
    ckan.logic.action.get.revision_show while 'package_show' declaration is
    resolved with standard 'get_action' hook. Not sure which to use so these
    are tried.

    Either the ``id`` or the ``user_obj`` parameter must be given in data_dict.

    :param id: the id or name of the user (optional)
    :type id: string
    :param user_obj: the user dictionary of the user (optional)
    :type user_obj: user dictionary

    :rtype: dictionary

    '''
    model = context['model']

    id = data_dict.get('id',None)
    provided_user = data_dict.get('user_obj',None)
    if id:
        user_obj = model.User.get(id)
        context['user_obj'] = user_obj
        if user_obj is None:
            raise NotFound
    elif provided_user:
        context['user_obj'] = user_obj = provided_user
    else:
        raise NotFound

    _check_access('user_show',context, data_dict)

    user_dict = dictization.model_dictize.user_dictize(user_obj,context)

    revisions_q = model.Session.query(model.Revision
    ).filter_by(author=user_obj.name)

    revisions_list = []
    for revision in revisions_q.limit(20).all():
        revision_dict = get.revision_show(context,{'id':revision.id})
        revision_dict['state'] = revision.state
        revisions_list.append(revision_dict)
    user_dict['activity'] = revisions_list

    user_dict['datasets'] = []
    dataset_q = model.Session.query(model.Package).join(model.PackageRole
    ).filter_by(user=user_obj, role=model.Role.ADMIN
    ).limit(50)

    for dataset in dataset_q:
        try:
            dataset_dict = logic.get_action('package_show')(context,
                                                            {'id': dataset.id})
        except logic.NotAuthorized:
            continue
        user_dict['datasets'].append(dataset_dict)

    user_dict['num_followers'] = logic.get_action('user_follower_count')(
        {'model': model, 'session': model.Session},
        {'id': user_dict['id']})

    # Added in ckanext-shibboleth
    extra_dict = utils.fetch_user_extra(user_dict['id'])
    user_dict.update(extra_dict)

    return user_dict


def user_update(context, data_dict):
    '''Update a user account.

    Minor rewrite to update also additional user profile information (acquired
    eg. from shibboleth).

    Normal users can only update their own user accounts. Sysadmins can update
    any user account.

    For further parameters see ``user_create()``.

    :param data_dict['id']: the name or id of the user to update
    :type data_dict['id']: string

    :returns: the updated user account
    :rtype: dictionary

    '''
    model = context['model']
    user = context['user']
    session = context['session']
    schema = context.get('schema') or ckan.logic.schema.default_update_user_schema()
    # Added in ckanext-shibboleth
    schema = utils.shibboleth_user_edit_form_schema(schema)

    id = _get_or_bust(data_dict, 'id')

    user_obj = model.User.get(id)
    context['user_obj'] = user_obj
    if user_obj is None:
        raise NotFound('User was not found.')

    _check_access('user_update', context, data_dict)

    data, errors = _validate(data_dict, schema, context)
    if errors:
        session.rollback()
        raise ValidationError(errors)

    user = dictization.model_save.user_dict_save(data, context)
    # Added in ckanext-shibboleth
    user_extras = utils.user_extra_save(data, context)

    activity_dict = {
        'user_id': user.id,
        'object_id': user.id,
        'activity_type': 'changed user',
        }
    activity_create_context = {
        'model': model,
        'user': user,
        'defer_commit':True,
        'session': session
    }
    _get_action('activity_create')(activity_create_context, activity_dict, ignore_auth=True)
    # TODO: Also create an activity detail recording what exactly changed in
    # the user.

    if not context.get('defer_commit'):
        model.repo.commit()
    return dictization.model_dictize.user_dictize(user, context)