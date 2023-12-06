from django.conf import settings

from rspsrv.apps.call.apps.base import EndingCause
from rspsrv.apps.call.apps.playback.core import Playback


class ExtensionPlayback(object):
    @staticmethod
    def not_exists(channel, next=None):
        return Playback(channel=channel, target_number="0", media=settings.DEFAULT_PLAYBACK['EXTENSION_NOT_EXISTS'],
                        next=next, cause=EndingCause.CALLEE_NEXISTS)

    @staticmethod
    def not_available(channel, next=None):
        return Playback(channel=channel, target_number="0", media=settings.DEFAULT_PLAYBACK['EXTENSION_NOT_AVAILABLE'],
                        next=next, cause=EndingCause.CALLEE_NAVAILABLE)


class ExternalPlayback(object):
    class Ending(object):
        @staticmethod
        def playback(channel, cause_code, next=None):
            return Playback(
                channel=channel,
                target_number="0",
                media="EXTERNAL_ENDING_%s" % cause_code,
                next=next,
                cause=EndingCause.CALLEE_DESTROYED,
            )

    @staticmethod
    def call_not_possible(channel, next=None, cause=EndingCause.CALL_RESTRICTED):
        return Playback(channel=channel, target_number="0", media=settings.DEFAULT_PLAYBACK['CALL_NOT_POSSIBLE'],
                        next=next, cause=cause)

    @staticmethod
    def outbound_disabled(
            channel,
            next=None,
            cause=EndingCause.OUTBOUND_DISABLED
    ):
        return Playback(
            channel=channel,
            target_number="0",
            media=settings.DEFAULT_PLAYBACK['OUTBOUND_DISABLED'],
            next=next,
            cause=cause,
        )

class PriceToSpeech:
    PriceLevel = {
        0: 'rial',
        1: 'thousand',
        2: 'million',
        3: 'milliard',
        4: 'billion'
    }

    def __init__(self, price, channel):
        if not isinstance(price, int):
            raise ValueError

        self.price = price
        self.channel = channel
        self.chained_playback = list()
        self.parsed_price = list()

    def split_price(self):
        while self.price > 0:
            self.parsed_price.append(self.price % 1000)
            self.price = int(self.price / 1000)

    def chain_playback(self):
        if self.price <= 0:
            # 0
            pb = Playback(channel=self.channel, media=settings.DEFAULT_PLAYBACK['CALL_NOT_POSSIBLE'])
            self.chained_playback.append(pb)

            # rial
            pb = Playback(channel=self.channel, media=settings.DEFAULT_PLAYBACK['CALL_NOT_POSSIBLE'])
            self.chained_playback.append(pb)

            return self.chained_playback

        self.split_price()

        for index in range(len(self.parsed_price) - 1, -1, -1):
            price = self.parsed_price[index]
            ones = price % 10
            tens = int(price / 10) % 10
            hundreds = int(price / 100) % 10

            if hundreds:
                pb = Playback(channel=self.channel, media=settings.DEFAULT_PLAYBACK['CALL_NOT_POSSIBLE'])
                self.chained_playback.append(pb)
                print(hundreds)

            if tens == 1:
                twos = price % 100
                pb = Playback(channel=self.channel, media=settings.DEFAULT_PLAYBACK['CALL_NOT_POSSIBLE'])
                self.chained_playback.append(pb)
                print(twos)

            else:
                if tens:
                    pb = Playback(channel=self.channel, media=settings.DEFAULT_PLAYBACK['CALL_NOT_POSSIBLE'])
                    self.chained_playback.append(pb)
                    print(tens)
                if ones:
                    pb = Playback(channel=self.channel, media=settings.DEFAULT_PLAYBACK['CALL_NOT_POSSIBLE'])
                    self.chained_playback.append(pb)
                    print(ones)

            # index
            pb = Playback(channel=self.channel, media=settings.DEFAULT_PLAYBACK['CALL_NOT_POSSIBLE'])
            self.chained_playback.append(pb)
            print(PriceToSpeech.PriceLevel[index])

        return self.chained_playback
