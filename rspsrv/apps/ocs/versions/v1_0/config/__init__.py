class OcsConfiguration:

    class URLs:
        DESTINATIONS = 'api/finance/v1/destinations/names/'
        RUNTIME_CONFIGS = 'api/finance/v1/runtime-configs/'
        CREDIT_SUBSCRIPTION = 'api/finance/v1/subscriptions/{sid}/credit/'
        BASE_BALANCE_SUBSCRIPTION = \
            'api/finance/v1/subscriptions/{sid}/base-balance/'
        CONVERT_SUBSCRIPTION = 'api/finance/v1/subscriptions/{sid}/convert/'
        DEALLOCATE_SUBSCRIPTION = 'api/finance/v1/subscriptions/{' \
                                  'sid}/deallocate/'
        SUBSCRIPTIONS_ANTI = 'api/finance/v1/anti-subscriptions/'
        SUBSCRIPTIONS = 'api/finance/v1/subscriptions/'
        CUSTOMER = 'api/finance/v1/customers/{cid}/'
        CUSTOMERS = 'api/finance/v1/customers/'
        SUBSCRIPTIONS_WITH_CUSTOMER = \
            'api/finance/v1/customers/{cid}/subscriptions/'
        SUBSCRIPTIONS_WITH_CUSTOMER_ANTI = \
            'api/finance/v1/customers/{cid}/anti-subscriptions/'
        SUBSCRIPTION_DEBIT_BALANCE = \
            'api/finance/v1/subscriptions/{sid}/debit-balance/'
        SUBSCRIPTION_ADD_BALANCE = \
            'api/finance/v1/subscriptions/{sid}/add-balance/'
        AVAILABILITY_SUBSCRIPTION = \
            'api/finance/v1/subscriptions/{sid}/availability/'
        SUBSCRIPTION = \
            'api/finance/v1/subscriptions/{sid}/'
        SUBSCRIPTION_WITH_CUSTOMER = \
            'api/finance/v1/customers/{cid}/subscriptions/{sid}/'

    class APILabels:
        DEALLOCATION = "Deallocation"
        PERIODIC_INVOICE = 'Periodic invoice'
        INTERIM_INVOICE = 'Interim invoice'
        AUTO_PAY_INTERIM_INVOICE = 'Auto pay interim invoice'
        MAX_USAGE = 'Max usage'
        DUE_DATE = 'Due date'
        EIGHTY_PERCENT = 'Eighty percent'
        PREPAID_EXPIRED = 'Prepaid expired'
        PREPAID_RENEWED = 'Prepaid renewed'
        EIGHTY_PERCENT_PREPAID = 'Prepaid eighty percent'
        MAX_USAGE_PREPAID = 'Max usage prepaid'


