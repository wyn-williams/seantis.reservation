from zope import schema
from zope.interface import Interface
from zope.component import getUtility

from plone.z3cform import layout
from plone.registry.interfaces import IRegistry
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper

from seantis.reservation import _

class ISeantisReservationSettings(Interface):

    throttle_minutes = schema.Int(
        title=_(u"Reservation throttling"),
        description=_(u'The number of minutes a user needs to wait between reservations')
    )

    confirm_reservation = schema.Bool(
        title=_(u"Confirm Reservation"),
        description=_(u'If true each reservation needs to be confirmed manually. This needs to be true to enable waiting lists.')
    )

def get(name):
    registry = getUtility(IRegistry)
    settings = registry.forInterface(ISeantisReservationSettings)
    assert hasattr(settings, name), "Unknown setting: %s" % name
    return getattr(settings, name)


class SeantisReservationSettingsPanelForm(RegistryEditForm): 
    schema = ISeantisReservationSettings
    label = _(u"Seantis Reservation Control Panel")
    
SeantisReservationControlPanelView = layout.wrap_form(
        SeantisReservationSettingsPanelForm, ControlPanelFormWrapper
    )