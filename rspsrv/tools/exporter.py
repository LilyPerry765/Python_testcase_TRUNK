from wkhtmltopdf.views import PDFTemplateResponse


class Exporter(PDFTemplateResponse):
    def __init__(self, request, cmd_options=None, *args, **kwargs):
        super(Exporter, self).__init__(request, cmd_options, *args, **kwargs)

        self.request = request
        self.cmd_options = cmd_options

    def export(self, filename, template, data=None, extension='pdf'):
        response = PDFTemplateResponse(
            request=self.request,
            template=template,
            filename='{filename}.{extension}'.format(filename=filename, extension=extension),
            context=data,
            show_content_in_browser=False,
            cmd_options=self.cmd_options,
        )

        return response
