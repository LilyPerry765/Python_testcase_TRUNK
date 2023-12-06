from django.conf import settings
from django.urls import reverse


class DirectorySearch(object):
    @staticmethod
    def generate_directory_xml(user_list):
        """
        Generates the XML required to display the phone directory from
        the list of DirectoryEntry instances given as a parameter.
        """
        xml = "<CiscoIPPhoneDirectory>\n"
        xml += "\t<Title>%s directory</Title>\n" % getattr(settings, 'RSP_ASCII_NAME', 'Respina')
        xml += "\t<Prompt>Select an entry.</Prompt>\n"
        for user in user_list:
            xml += "\t<DirectoryEntry>\n"
            xml += "\t\t<Name>%s</Name>\n" % user[0]
            xml += "\t\t<Telephone>%s</Telephone>\n" % user[1]
            xml += "\t</DirectoryEntry>\n"
        xml += "</CiscoIPPhoneDirectory>\n"

        return xml

    @staticmethod
    def generate_search_xml():
        """
        Generates the XML required to display a phone directory search
        page on the Cisco 79xx IP phones.
        """

        xml = "<CiscoIPPhoneInput>\n"
        xml += "\t<Title>Search for an entry</Title>\n"
        xml += "\t<Prompt>Enter a search keyword.</Prompt>\n"
        xml += "\t<URL>%s%s</URL>\n" % (settings.RESPINA_DIRECTORY_BASE_ADDRESS, reverse('endpoint:directory_search'))
        xml += "\t<InputItem>\n"
        xml += "\t\t<DisplayName>Keyword</DisplayName>\n"
        xml += "\t\t<QueryStringParam>keyword</QueryStringParam>\n"
        xml += "\t\t<InputFlags></InputFlags>\n"
        xml += "\t\t<DefaultValue></DefaultValue>\n"
        xml += "\t</InputItem>\n"
        xml += "</CiscoIPPhoneInput>\n"

        return xml
