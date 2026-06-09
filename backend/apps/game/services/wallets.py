from __future__ import annotations

from typing import Protocol

from apps.game.i18n import DEFAULT_LOCALE

from .money import MoneyService

# Канонические ключи валют. Совпадают со значениями ShopPurchase.PaymentCurrency
# и ключами payload "balances" — держим их согласованными.
MONEY_COPPER = "money_copper"
PREMIUM_CURRENCY = "premium_currency"


class Wallet(Protocol):
    """Единый интерфейс кошелька одной валюты пользователя.

    Адаптеры закрывают конкретный сервис-кошелёк (медь/премиум) одним швом:
    балансы читаются, движения проходят через grant/charge с леджером.
    """

    key: str

    def get_balance(self, user) -> int: ...

    def grant(self, user, *, amount: int, reason: str, metadata=None, idempotency_key=None): ...

    def charge(
        self,
        user,
        *,
        amount: int,
        reason: str,
        metadata=None,
        idempotency_key=None,
        insufficient_message: str = "not_enough_money",
        locale: str = DEFAULT_LOCALE,
    ): ...


class CopperWallet:
    """Адаптер кошелька медных монет поверх MoneyService."""

    key = MONEY_COPPER

    def get_balance(self, user) -> int:
        return MoneyService.get_amount(user)

    def grant(self, user, **kwargs):
        return MoneyService.grant(user=user, **kwargs)

    def charge(self, user, **kwargs):
        return MoneyService.charge(user=user, **kwargs)


class PremiumWallet:
    """Адаптер кошелька премиум-валюты поверх PremiumCurrencyService."""

    key = PREMIUM_CURRENCY

    @staticmethod
    def _service():
        # Ленивый импорт: billing зависит от game, не наоборот.
        from apps.billing.services import PremiumCurrencyService

        return PremiumCurrencyService

    def get_balance(self, user) -> int:
        return self._service().get_amount(user)

    def grant(self, user, **kwargs):
        return self._service().grant(user=user, **kwargs)

    def charge(self, user, **kwargs):
        return self._service().charge(user=user, **kwargs)


_WALLETS: dict[str, Wallet] = {wallet.key: wallet for wallet in (CopperWallet(), PremiumWallet())}


def get_wallet(currency_key: str) -> Wallet:
    """Возвращает кошелёк по ключу валюты; бросает по неизвестному ключу."""

    try:
        return _WALLETS[currency_key]
    except KeyError as exc:
        raise ValueError(f"Unknown currency: {currency_key!r}") from exc


def all_balances(user) -> dict[str, int]:
    """Возвращает балансы всех валют для payload ответов."""

    return {key: wallet.get_balance(user) for key, wallet in _WALLETS.items()}
