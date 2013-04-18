import logging
log = logging.getLogger('seantis.reservation')

from functools import wraps

from alembic.migration import MigrationContext
from alembic.operations import Operations

from sqlalchemy import types
from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy import Table
from sqlalchemy.schema import Column

from Products.CMFCore.utils import getToolByName
from zope.component import getUtility

from seantis.reservation import utils
from seantis.reservation.models import customtypes
from seantis.reservation.session import ISessionUtility


def db_upgrade(fn):

    @wraps(fn)
    def wrapper(context):
        util = getUtility(ISessionUtility)
        dsn = util.get_dsn(utils.getSite())

        engine = create_engine(dsn, isolation_level='SERIALIZABLE')
        connection = engine.connect()
        transaction = connection.begin()
        try:
            context = MigrationContext.configure(connection)
            operations = Operations(context)

            metadata = MetaData(bind=engine)

            fn(operations, metadata)

            transaction.commit()

        except:
            transaction.rollback()
            raise

        finally:
            connection.close()

    return wrapper


def recook_js_resources(context):
    getToolByName(context, 'portal_javascripts').cookResources()


def recook_css_resources(context):
    getToolByName(context, 'portal_css').cookResources()


@db_upgrade
def upgrade_to_1001(operations, metadata):

    # Check whether column exists already (happens when several plone sites
    # share the same SQL DB and this upgrade step is run in each one)

    reservations_table = Table('reservations', metadata, autoload=True)
    if 'session_id' not in reservations_table.columns:
        operations.add_column(
            'reservations', Column('session_id', customtypes.GUID())
        )


@db_upgrade
def upgrade_1001_to_1002(operations, metadata):

    reservations_table = Table('reservations', metadata, autoload=True)
    if 'quota' not in reservations_table.columns:
        operations.add_column(
            'reservations', Column(
                'quota', types.Integer(), nullable=False, server_default='1'
            )
        )


@db_upgrade
def upgrade_1002_to_1003(operations, metadata):

    allocations_table = Table('allocations', metadata, autoload=True)
    if 'reservation_quota_limit' not in allocations_table.columns:
        operations.add_column(
            'allocations', Column(
                'reservation_quota_limit',
                types.Integer(), nullable=False, server_default='0'
            )
        )


def upgrade_1003_to_1004(context):

    # 1004 untangles the dependency hell that was default <- sunburst <- izug.
    # Now, sunburst and izug.basetheme both have their own profiles.

    # Since the default profile therefore has only the bare essential styles
    # it needs to be decided on upgrade which theme was used, the old css
    # files need to be removed and the theme profile needs to be applied.

    # acquire the current theme
    skins = getToolByName(context, 'portal_skins')
    theme = skins.getDefaultSkin()

    # find the right profile to use
    profilemap = {
        'iZug Base Theme': 'izug_basetheme',
        'Sunburst Theme': 'sunburst'
    }

    if theme not in profilemap:
        log.info("Theme %s is not supported by seantis.reservation" % theme)
        profile = 'default'
    else:
        profile = profilemap[theme]

    # remove all existing reservation stylesheets
    css_registry = getToolByName(context, 'portal_css')
    stylesheets = css_registry.getResourcesDict()
    ids = [i for i in stylesheets if 'resource++seantis.reservation.css' in i]

    map(css_registry.unregisterResource, ids)

    # reapply the chosen profile

    setup = getToolByName(context, 'portal_setup')
    setup.runAllImportStepsFromProfile(
        'profile-seantis.reservation:%s' % profile
    )


def upgrade_1004_to_1005(context):

    setup = getToolByName(context, 'portal_setup')
    setup.runImportStepFromProfile(
        'profile-seantis.reservation:default', 'typeinfo'
    )


def upgrade_1005_to_1006(context):

    # remove the old custom fullcalendar settings
    css_registry = getToolByName(context, 'portal_css')

    old_definitions = [
        '++resource++seantis.reservation.js/fullcalendar.js'
        '++resource++collective.js.fullcalendar/fullcalendar.min.js'
        '++resource++collective.js.fullcalendar/fullcalendar.gcal.js'
    ]
    map(css_registry.unregisterResource, old_definitions)

    # reapply the fullcalendar profile
    setup = getToolByName(context, 'portal_setup')

    setup.runAllImportStepsFromProfile(
        'profile-collective.js.fullcalendar:default'
    )

    recook_css_resources(context)
    recook_js_resources(context)
