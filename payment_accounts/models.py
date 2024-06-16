from __future__ import annotations

from decimal import Decimal
from django.db import models, transaction
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from .exceptions import DuplicateError


def is_amount_positive(method):
    def wrapper(cls, *args, **kwargs):
        amount = kwargs['amount']
        if amount < 0:
            raise ValueError('Should be positive value')
        return method(cls, *args, **kwargs)
    return wrapper


class Account(models.Model):
    user_uid = models.UUIDField(unique=True, editable=False, db_index=True)
    balance = models.DecimalField(
        decimal_places=2,
        max_digits=settings.MAX_BALANCE_DIGITS,
        validators=[MinValueValidator(0, message='Insufficient Funds')],
        default=0,
    )

    @classmethod
    @is_amount_positive
    def deposit(cls, *, pk: int, amount: Decimal) -> Account:
        """
        Use a classmethod instead of an instance method,
        to acquire the lock we need to tell the database
        to lock it, preventing data update collisions.
        When operating on self the object is already fetched.
        And we don't have  any guaranty that it was locked.
        """
        with transaction.atomic():
            account = get_object_or_404(
                cls.objects.select_for_update(),
                pk=pk,
            )
            account.balance += amount
            account.save()
        return account

    @classmethod
    @is_amount_positive
    def withdraw(cls, *, pk: int, amount: Decimal) -> Account:
        with transaction.atomic():
            account = get_object_or_404(
                cls.objects.select_for_update(),
                pk=pk,
            )
            account.balance -= amount
            account.save()
        return account

    def __str__(self) -> str:
        return f'User id: {self.user_uid}'


message_for_min_validators = 'Should be positive value'


class BalanceChange(models.Model):
    class TransactionType(models.TextChoices):
        WITHDRAW = ('WD', 'WITHDRAW')
        DEPOSIT = ('DT', 'DEPOSIT')

    account_id = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='balance_changes',
    )
    amount = models.DecimalField(
        max_digits=settings.MAX_BALANCE_DIGITS,
        validators=[MinValueValidator(0, message=message_for_min_validators)],
        decimal_places=2,
        editable=False,
    )
    date_time_creation = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        db_index=True,
    )
    is_accepted = models.BooleanField(default=False)
    operation_type = models.CharField(max_length=20, choices=TransactionType.choices)

    def __str__(self) -> str:
        return (
            f'Account id:  {self.account_id} '
            f'Date time of creation: {self.date_time_creation}'
            f'Amount: {self.amount}'
        )

    class Meta:
        ordering = ['-date_time_creation']


class TransferHistory(models.Model):
    account_from = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name='history_accounts_from',
    )
    account_to = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name='history_accounts_to',
    )
    amount = models.DecimalField(
        decimal_places=2,
        max_digits=settings.MAX_BALANCE_DIGITS,
        validators=[MinValueValidator(0, message=message_for_min_validators)],
        editable=False,
    )
    date_time_creation = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        db_index=True,
    )

    def clean(self):
        if self.account_from == self.account_to:
            raise DuplicateError(
                'account_from and account_to should be different values',
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return (
            f'Account from: {self.account_from} -> '
            f'Account to: {self.account_to}'
            f'Date time of creation: {self.date_time_creation}'
        )

    class Meta:
        ordering = ['-date_time_creation']


class Transaction(models.Model):
    MAX_ITEM_PRICE = 10000  # in case of mistake

    account_from = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name='transactions_account_from',
    )
    account_to = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name='transactions_account_to',
    )
    item_price = models.DecimalField(
        decimal_places=2,
        max_digits=settings.MAX_BALANCE_DIGITS,
        validators=[
            MinValueValidator(0, message=message_for_min_validators),
            MaxValueValidator(
                MAX_ITEM_PRICE,
                message=f'Should be not greater than {MAX_ITEM_PRICE}',
            ),
        ],
    )
    item_uid = models.UUIDField(editable=False, db_index=True)
    is_frozen = models.BooleanField(default=False)
    is_accepted = models.BooleanField(default=False)

    def __str__(self) -> str:
        return (
            f'Account from: {self.account_from} -> '
            f'Account to: {self.account_to} '
            f'Item_uid: {self.item_uid}'
        )


class TransactionHistory(models.Model):
    class TransactionType(models.TextChoices):
        CREATED = ('CT', 'CREATED')
        COMPLETED = ('CD', 'COMPLETED')

    transaction_id = models.ForeignKey(
        Transaction,
        on_delete=models.PROTECT,
        related_name='transactions_history',
        editable=False,
    )
    date_time_creation = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        db_index=True,
    )
    operation_type = models.CharField(max_length=50, choices=TransactionType.choices)

    def __str__(self) -> str:
        return (
            f'Transaction_id: {self.transaction_id}'
            f'Date time of creation: {self.date_time_creation}'
        )

    class Meta:
        ordering = ['-date_time_creation']
