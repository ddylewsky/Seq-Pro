from typing import List, Dict


class AssetBacked:

    def __init__(self, tranches: List[float]):
        self.tranches = tranches  # an array of bond balances in order of seniority
        self.payment_amount = 0.0


class AssetBackedSequential(AssetBacked):

    def sequential_payment(self, amount: float, specific_tranches: List[int] = None) -> None:
        """
        Method to apply a principal payment in order of seniority.
        :param amount: Amount of the payment
        :param specific_tranches: a list of the indexes of the tranches to be included in the payment. If None all
        tranches will be included
        :return: The amount left after the payment is applied
        """
        self.payment_amount += amount
        if specific_tranches is None:
            specific_tranches = [i for i in range(len(self.tranches))]  # include all tranches
        current_tranche = 0  # start with first tranche
        while self.payment_amount > 0 and current_tranche <= len(specific_tranches) - 1:
            tranche_idx = specific_tranches[current_tranche]
            current_balance = self.tranches[tranche_idx]
            if self.payment_amount >= current_balance:
                self.tranches[tranche_idx] = 0
                self.payment_amount -= current_balance
            else:
                self.tranches[tranche_idx] -= self.payment_amount
                self.payment_amount -= current_balance

            current_tranche += 1


class AssetBackedProRata(AssetBacked):

    def pro_rata_payment(self, amount: float, specific_tranches: List[int] = None) -> None:
        """
        Method to apply a pro-rata principal payment.
        :param amount: Amount of payment
        :param specific_tranches: a list of the indexes of the tranches to be included in the payment. If None all
        tranches will be included
        :return: The amount left after the payment is applied
        """
        # TODO add code to handle cases where payment is greater than total balances
        _total_amount = self.payment_amount + amount  # temp variable to keep track of payment amounts
        self.payment_amount += amount
        if specific_tranches is None:  # check if all tranches should be included
            total_balance = sum(self.tranches)
            for idx in range(len(self.tranches)):
                tranche_portion = self.tranches[idx] / total_balance * _total_amount
                self.tranches[idx] -= tranche_portion
                self.payment_amount -= tranche_portion
        else:
            total_balance = 0
            for idx in range(len(self.tranches)):  # calculate total of included tranches
                if idx in specific_tranches:
                    total_balance += self.tranches[idx]
            for idx in specific_tranches:
                tranche_portion = self.tranches[idx] / total_balance * _total_amount
                self.tranches[idx] -= tranche_portion
                self.payment_amount -= tranche_portion


class AssetBackedNested(AssetBackedSequential, AssetBackedProRata):

    def nested_payments(self, payment_terms: Dict) -> None:

        payment_ = {
            'sequential': self.sequential_payment,
            'prorata': self.pro_rata_payment
        }

        payment_amount = payment_terms.get('amount')
        specific_tranches = payment_terms.get('specificTranches')
        payment_type = payment_terms.get('paymentType')

        try:
            payment_[payment_type](payment_amount, specific_tranches)  # payment_type is directly looked up by key to
            # produce KeyError for payments_types not implemented in the base classes

        except KeyError:
            print(f"Payment Type <{payment_type}> Not available for this asset backed class. The amount of "
                  f"<{payment_amount}> will be carried into next payment")
            self.payment_amount += payment_amount

        next_payment = payment_terms.get('nextPayment')
        if next_payment is not None:
            # process further payments carrying remainder amounts from previous payments into the next payment
            self.nested_payments(next_payment)
        else:
            # no further payments
            pass


s = AssetBackedNested([1000.0, 2000.0, 2000.0, 4000.0])

payments = {
    'paymentType': 'sequential',
    'amount': 2000.0,
    'specificTranches': [0],
    'nextPayment':
        {
            'paymentType': 'prorata',
            'amount': 0,
            'specificTranches': [1, 2]
        }
}
s.nested_payments(payments)
assert s.tranches == [0.0, 1500.0, 1500.0, 4000.0]
print(s.tranches)

s2 = AssetBackedNested([1000.0, 2000.0, 2000.0, 4000.0])
payments = {
    'paymentType': 'prorata',
    'amount': 2000.0,
    'nextPayment':
        {
            'paymentType': 'sequential',
            'amount': 1000,
            'specificTranches': [0, 3]
        }
}
s2.nested_payments(payments)
print(s2.tranches)  # [0, 1555.56, 1555.56, 2888.89]

s3 = AssetBackedNested([1000.0, 2000.0, 2000.0, 4000.0])
payments = {
    'paymentType': 'creditEvent',
    'amount': 2000.0,
    'nextPayment':
        {
            'paymentType': 'sequential',
            'amount': 1000,
            'specificTranches': [0, 3]
        }
}
s3.nested_payments(payments)
print(s3.tranches)  # First payment credit event does not get processed and the 2,000 payment is carried into
# the sequential payment to the first and last tranches [0.0, 2000.0, 2000.0, 2000.0]
