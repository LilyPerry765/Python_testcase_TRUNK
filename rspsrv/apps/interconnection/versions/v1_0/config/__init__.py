class InterconnectionConfiguration:
    class URLs:
        OPERATORS = 'api/finance/v1/operators/'
        OPERATOR = 'api/finance/v1/operators/{op}/'
        PROFITS = 'api/finance/v1/profits/'
        EXPORT_PROFITS = 'api/finance/v1/export/{ex_type}/profits/'
        PROFIT = 'api/finance/v1/profits/{pr}/'

    class APILabels:
        CREATE_OPERATOR = "Create operator"
        UPDATE_OPERATOR = "Update operator"
        DELETE_OPERATOR = "Delete operator"
        CREATE_PROFIT = "Create profit"
        UPDATE_PROFIT = "Update profit"
