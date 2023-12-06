# @TODO: Deprecated
import logging

import xlrd
from django.core.management.base import BaseCommand

from rspsrv.apps.subscription.models import Subscription

logger = logging.getLogger("common")


class Command(BaseCommand):
    help = 'Import credits from Excel file'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Absolute path to excel file'
        )
        parser.add_argument(
            'subscription_column',
            type=str,
            help='Column name of subscription code'
        )
        parser.add_argument(
            'credit_column',
            type=str,
            help='Column name of credit'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        subscription_column = options['subscription_column']
        credit_column = options['credit_column']
        sheet = None
        updated_count = 0
        try:
            work_book = xlrd.open_workbook(file_path)
            sheet = work_book.sheet_by_index(0)
            sheet.cell_value(0, 0)
        except Exception as e:
            self.stderr.write(str(e))

        if sheet:
            subscription_index = -1
            credit_index = -1
            for cell_index in range(sheet.ncols):
                if sheet.cell_value(0, cell_index) == subscription_column:
                    subscription_index = cell_index
                if sheet.cell_value(0, cell_index) == credit_column:
                    credit_index = cell_index
            if subscription_index == -1 or credit_index == -1:
                self.stderr.write(
                    "Subscription and credit column does not exists!",
                )
            else:
                for row_index in range(0, sheet.nrows):
                    if sheet.cell_type(
                        row_index,
                        subscription_index,
                    ) != 1:
                        subscription_code = str(sheet.cell_value(
                            row_index,
                            subscription_index,
                        )).strip().split(".")[0]
                    else:
                        subscription_code = str(sheet.cell_value(
                            row_index,
                            subscription_index,
                        )).strip()
                    credit = str(
                        sheet.cell_value(row_index, credit_index)
                    ).strip()
                    try:
                        subscription_object = Subscription.objects.get(
                            subscription_code=subscription_code,
                        )
                        subscription_object.gateway_credit = int(float(credit))
                        subscription_object.save()
                        updated_count += 1
                    except (Subscription.DoesNotExist, ValueError) as e:
                        logger.error(
                            "{}: {}".format(subscription_code, e)
                        )
                logger.error(
                    "{} of {} credits are updated".format(
                        updated_count,
                        sheet.nrows
                    )
                )
