from zope.interface import implements

from seantis.reservation.reservations import combine_reservations
from seantis.reservation.interfaces import (
    IResourceViewedEvent,
    IReservationsBaseEvent,
    IReservationsMadeEvent,
    IReservationsApprovedEvent,
    IReservationsDeniedEvent,
    IReservationsRevokedEvent,
    IReservationsConfirmedEvent
)


class ResourceViewedEvent(object):
    implements(IResourceViewedEvent)

    def __init__(self, context):
        self.context = context


class ReservationsBaseEvent(object):
    implements(IReservationsBaseEvent)

    def __init__(self, reservations, language):
        self.reservations = reservations
        self.language = language

        combined = tuple(combine_reservations(reservations))
        assert len(combined) == 1
        self.reservation = combined[0]


class ReservationsMadeEvent(ReservationsBaseEvent):
    implements(IReservationsMadeEvent)


class ReservationsApprovedEvent(ReservationsBaseEvent):
    implements(IReservationsApprovedEvent)


class ReservationsDeniedEvent(ReservationsBaseEvent):
    implements(IReservationsDeniedEvent)


class ReservationsRevokedEvent(ReservationsBaseEvent):
    implements(IReservationsRevokedEvent)

    def __init__(self, reservations, language, reason, send_email):
        super(ReservationsRevokedEvent, self).__init__(reservations, language)
        self.reason = reason
        self.send_email = send_email


class ReservationsConfirmedEvent(object):
    implements(IReservationsConfirmedEvent)

    def __init__(self, reservations, language):
        self.reservations = reservations
        self.language = language
