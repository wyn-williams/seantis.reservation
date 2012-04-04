from zope.security import checkPermission
from zope.component import getMultiAdapter

from seantis.reservation.utils import is_uuid, get_resource_by_uuid
from seantis.reservation.timeframe import timeframes_by_context

def for_allocations(context, resources):
    """Returns a function which takes an allocation and returns true if the
    allocation can be exposed.

    resources can be a list of uuids or a list of resource objects

    """

    # get a dictionary with uuids as keys and resources as values
    def get_object(obj):
        if is_uuid(obj):
            return obj, get_resource_by_uuid(context, obj)
        else:
            return obj.uuid(), obj

    resource_objects = dict([get_object(o) for o in resources])

    # get timeframes for each uuid
    timeframes = {}
    for uuid, resource in resource_objects.items():

        # Don't load the timeframes of the resources for which the user has
        # special access to. This way they won't get checked later in 'is_exposed'
        if checkPermission('seantis.reservation.ViewHiddenAllocations', resource):
            timeframes[uuid] = []
        else:
            timeframes[uuid] = timeframes_by_context(resource)

    # returning closure
    def is_exposed(allocation):

        # use the mirror_of as resource-keys of mirrors do not really exist
        # as plone objects
        frames = timeframes[str(allocation.mirror_of)]

        if not frames:
            return True

        # the start date is relevant
        day = allocation.start.date()
        for frame in frames:
            if frame.start <= day and day <= frame.end:
                return frame.visible()

        return False

    return is_exposed

def for_views(context, request):
    """Returns a function which takes a viewname and returns true if the user
    has the right to see the view.

    """

    #gets an instance of the view
    get_view = lambda name: getMultiAdapter((context, request), name=name)

    def is_exposed(viewname):
        view = get_view(viewname)
        assert hasattr(view, 'permission'), "missing permission attribute"
        
        return checkPermission(view.permission, view)

    return is_exposed

def for_calendar(resource):
    """Returns a function which takes a calendar option and returns true
    if it is enabled.

    """

    # right now there's nothing sophisticated to see here
    def is_exposed(option):
        return checkPermission('cmf.ManagePortal', resource)

    return is_exposed