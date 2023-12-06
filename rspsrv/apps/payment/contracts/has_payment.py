class HasPaymentContract:
    def __init__(self):
        pass

    def set_state_to_pending(self, *args, **kwargs):
        raise NotImplementedError('set_state_to_pending method not implemented.')

    def set_state_to_ready_to_pay(self, *args, **kwargs):
        raise NotImplementedError('set_state_to_ready_to_pay not implemented.')

    def set_state_to_paid(self, *args, **kwargs):
        raise NotImplementedError('set_state_to_success not implemented.')
