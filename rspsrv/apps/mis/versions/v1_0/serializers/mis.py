# --------------------------------------------------------------------------
# Serialize retrieved data from MIS
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - mis.py
# Created at 2020-6-29,  9:15:14
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------


class IncorporationTransformer:
    @staticmethod
    def from_raw(raw):
        """

        :param raw:
        :return:
        """
        if not raw:
            return None

        return {
            'account_name': raw.get('AccountName'),
            'register_number': raw.get('RegisterNumber'),
            'national_code_manager': raw.get('NationalCodeManager'),
            'postal_code': raw.get('PostalCode'),
            'address': raw.get('Address'),
            'email': raw.get('Email'),
            'finance_code': raw.get('FinanceCode'),
            'mobile': raw.get('Mobile'),
            'nexfon': NexfonInfoTransformer.from_raw(
                raw.get('nexfon', {})
            ),
        }

    @staticmethod
    def to_raw(data):
        """

        :param data:
        :return:
        """
        pass


class NexfonInfoTransformer:
    """
    Nexfon field in the body.
    """

    @staticmethod
    def from_raw(raw):
        """

        :param raw:
        :return:
        """
        if not raw:
            return None

        return {
            'mobile': raw.get('NexfonMobile'),
            'email': raw.get('NexfonEmail'),
        }

    @staticmethod
    def to_raw(data):
        """

        :param data:
        :return:
        """
        pass


class NaturalTransformer:
    """
    Doc.
    """

    @staticmethod
    def from_raw(raw):
        """

        :param raw:
        :return:
        """
        if not raw:
            return None

        return {
            'first_name': raw.get('FirstName'),
            'last_name': raw.get('LastName'),
            'email': raw.get('Email'),
            'national_code': raw.get('NationalCode'),
            'address': raw.get('Address'),
            'postal_code': raw.get('PostalCode'),
            'mobile': raw.get('Mobile'),
            'nexfon': NexfonInfoTransformer.from_raw(
                raw.get('nexfon', {})
            ),
        }

    @staticmethod
    def to_raw(data):
        """

        :param data:
        :return:
        """
        pass


class ClientInfoTransformer:
    """
    Doc.
    """

    @staticmethod
    def from_raw(raw):
        """

        :param raw:
        :return:
        """
        if not raw:
            return None

        return {
            'type': raw.get('Type'),
            'natural_person': NaturalTransformer.from_raw(
                raw.get('NaturalPerson', {})
            ),
            'incorporation': IncorporationTransformer.from_raw(
                raw.get('Incorporation', {})
            ),
        }

    @staticmethod
    def to_raw(data):
        """

        :param data:
        :return:
        """
        pass
