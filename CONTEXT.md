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

**Premium top-up**:
An attempt to buy premium currency for real money. It owns the payment
lifecycle and the offer snapshot; only a succeeded top-up may create a premium
currency ledger movement.
_Avoid_: payment, premium purchase, transaction.

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

## Language — Hero storage

**Hero storage**:
A deep module that owns one item kind's count for a hero (ingredients, potions):
it self-locks the storage row and enforces the non-negative invariant. Borrows
the wallet's discipline but is *not* a currency — there is **no ledger**, and
movements are not audited. One generic `HeroStorage(model, fk_field)` in
`apps.game.services.storages` backs two instances: `INGREDIENT_STORAGE`
(`HeroIngredientStorage`) and `POTION_STORAGE` (`HeroPotionStorage`). Callers
never touch the `count` field directly.
_Avoid_: inventory (that is the equipment pack), bag, stash.

**deposit / withdraw**:
The two verbs every hero storage exposes. `deposit` adds count (get-or-creates
the row); `withdraw` removes it, enforces the non-negative invariant, and
returns the storage row with the new count. Deliberately distinct from the
wallet's **grant / charge** — storages are not currencies, so the verbs differ.
`withdraw` takes an `insufficient_message` and optional `missing_message` i18n
key so callers keep context-specific errors (`not_enough_potions`,
`potion_not_owned`, `not_enough_ingredients`). Batch issuance still crosses
this module through `deposit_many` / `deposit_for_characters`; callers do not
bulk-update `count` directly.
_Avoid_: grant/charge (reserved for wallets), add/spend, increment/decrement.

## Language — Dungeon Limits

**limit_category**:
A balance category shared by multiple dungeon locations for the purpose of a
common run limit. It is separate from `location_type`: `location_type` describes
how a location behaves, while `limit_category` describes which locations spend
from the same limit pool.
_Avoid_: dungeon type (ambiguous with behavior), location type.

## Language — Dungeon Runs

**Dungeon run**:
One concrete timed attempt by a hero in one location. A dungeon run may be
combat or resource-based, but it always occupies the hero's single active
activity slot until it is ready to be claimed.
_Avoid_: expedition, поход, activity.

**Auto run**:
A player-enabled mode that repeats one selected location by claiming the
finished dungeon run and starting that same location again until the first
blocking condition. It is not a separate hero activity, but while active or
stopping it reserves the hero's next dungeon run start.
_Avoid_: auto chain, auto repeat, автопрохождение.

**Armed auto run**:
The pre-start UI choice where one location is marked so the next manual run of
that same location starts an auto run. It is not an active server-side auto run
until the player starts the marked location.
_Avoid_: queued auto run, reserved run.

**Auto run summary**:
The result summary produced when an auto run stops. The player must acknowledge
an unread auto run summary before starting another dungeon run.
_Avoid_: notification, toast, report.
