class ExceptionsCode:
    SUCCESS_0 = '0'
    UNKNOWN_ERROR_1 = '1'
    MNP_2 = '2'
    DB_ERROR_3 = '3'
    NUMBER_NOT_IN_USE_4 = '4'
    INVALID_NUMBER_5 = '5'
    SUB_DEDICATED_RANGE_6 = '6'
    SERVICE_NOT_EXISTING_7 = '7'
    COMMUNICATION_NOT_ESTABLISHED_8 = '8'
    ZONE_ID_NOT_DEFINED_9 = '9'
    MORE_ANSWER_EXISTING_10 = '10'


class ResponsesCode:
    class ApplyForwardSettings:
        SUCCESS_0 = '0'
        ALREADY_SET_OR_UNSET_BY_YOURSELF_1 = '1'
        ALREADY_FORWARDED_TO_ANOTHER_NUMBER_2 = '2'
        IS_NOT_FORWARDED_RIGHT_NOW_3 = '3'
        FORWARD_THIS_NUMBER_IS_NOT_POSSIBLE_4 = '4'
        FORWARD_TO_THIS_NUMBER_IS_NOT_POSSIBLE_5 = '5'
        NO_NUMBERS_FORWARDED_TO_THIS_NUMBER_6 = '6'


class CallDirection:
    IN_OUT_0 = '0'
    OUTBOUND_1 = '1'
    INBOUND_2 = '2'


class ForwardTypes:
    ALL_CALLS_0 = '0'
    NO_ANSWER_CALLS_1 = '1'
    CALLEE_BUSY_2 = '2'
    CALLEE_NOT_AVAILABLE_3 = '3'


class TransactionID:
    REMOVE_FORWARD_1 = '1'
    ADD_FORWARD_0 = '0'


class SIAMConfigurations:
    class APILabels:
        GET_CDRS = "Get CDRs"
        GET_INVOICES = "Get invoices"
        UPDATE_FORWARD_SETTINGS = "Update forward settings"
        GET_FORWARD_SETTINGS = "Get forward settings"
        SUSPEND_PRODUCT = "Suspend product"
        GET_PRODUCT = "Get product"
        GET_NUMBERING_CAPACITY = "Get numbering capacity"
