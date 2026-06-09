# Browser Async RPG — Context

Domain vocabulary for the game's economy. Captures the deliberate language used
when reasoning about currency, so architecture reviews and new code stay
consistent.

## Language — Economy

**Wallet**:
A deep module that owns one currency's balance for a user: it holds the lock,
the non-negative invariant, and the ledger. Callers never touch the balance
field directly. Today there are two: the copper wallet (`MoneyService`) and the
premium wallet (`PremiumCurrencyService`).
_Avoid_: balance manager, currency handler.

**Copper** / **money_copper**:
The earned in-game currency, stored on `game.User.money_copper`. Mutated only
through `MoneyService`.
_Avoid_: gold, coins, money (unqualified).

**Premium currency**:
The purchased currency, stored on `billing.UserPremiumBalance.amount`. Mutated
only through `PremiumCurrencyService`.
_Avoid_: gems, hard currency.

**grant / charge**:
The two verbs every wallet exposes for mutation. `grant` adds currency;
`charge` removes it and enforces the non-negative invariant. Both write a ledger
row and return it.
_Avoid_: add/spend, deposit/withdraw, credit/debit.

**Ledger**:
The append-only, immutable record of every wallet movement
(`MoneyTransaction`, `PremiumCurrencyTransaction`): signed amount, reason,
`balance_after`, optional idempotency key. Admin-readonly, never edited or
deleted.
_Avoid_: history, audit log, journal.
