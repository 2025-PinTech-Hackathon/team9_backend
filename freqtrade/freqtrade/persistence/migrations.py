import logging

from sqlalchemy import Engine, inspect, select, text, update

from freqtrade.exceptions import OperationalException
from freqtrade.persistence.trade_model import Order, Trade


logger = logging.getLogger(__name__)


def get_table_names_for_table(inspector, tabletype: str) -> list[str]:
    return [t for t in inspector.get_table_names() if t.startswith(tabletype)]


def has_column(columns: list, searchname: str) -> bool:
    return len(list(filter(lambda x: x["name"] == searchname, columns))) == 1


def get_column_def(columns: list, column: str, default: str) -> str:
    return default if not has_column(columns, column) else column


def get_backup_name(tabs: list[str], backup_prefix: str):
    table_back_name = backup_prefix
    for i, table_back_name in enumerate(tabs):
        table_back_name = f"{backup_prefix}{i}"
        logger.debug(f"trying {table_back_name}")

    return table_back_name


def get_last_sequence_ids(engine, trade_back_name: str, order_back_name: str):
    order_id: int | None = None
    trade_id: int | None = None

    if engine.name == "postgresql":
        with engine.begin() as connection:
            trade_id = connection.execute(text("select nextval('trades_id_seq')")).fetchone()[0]
            order_id = connection.execute(text("select nextval('orders_id_seq')")).fetchone()[0]
        with engine.begin() as connection:
            connection.execute(
                text(f"ALTER SEQUENCE orders_id_seq rename to {order_back_name}_id_seq_bak")
            )
            connection.execute(
                text(f"ALTER SEQUENCE trades_id_seq rename to {trade_back_name}_id_seq_bak")
            )
    return order_id, trade_id


def set_sequence_ids(engine, order_id, trade_id, pairlock_id=None):
    if engine.name == "postgresql":
        with engine.begin() as connection:
            if order_id:
                connection.execute(text(f"ALTER SEQUENCE orders_id_seq RESTART WITH {order_id}"))
            if trade_id:
                connection.execute(text(f"ALTER SEQUENCE trades_id_seq RESTART WITH {trade_id}"))
            if pairlock_id:
                connection.execute(
                    text(f"ALTER SEQUENCE pairlocks_id_seq RESTART WITH {pairlock_id}")
                )


def drop_index_on_table(engine, inspector, table_bak_name):
    with engine.begin() as connection:
        # drop indexes on backup table in new session
        for index in inspector.get_indexes(table_bak_name):
            if engine.name == "mysql":
                connection.execute(text(f"drop index {index['name']} on {table_bak_name}"))
            else:
                connection.execute(text(f"drop index {index['name']}"))


def migrate_trades_and_orders_table(
    decl_base,
    inspector,
    engine,
    trade_back_name: str,
    cols: list,
    order_back_name: str,
    cols_order: list,
):
    base_currency = get_column_def(cols, "base_currency", "null")
    stake_currency = get_column_def(cols, "stake_currency", "null")
    fee_open = get_column_def(cols, "fee_open", "fee")
    fee_open_cost = get_column_def(cols, "fee_open_cost", "null")
    fee_open_currency = get_column_def(cols, "fee_open_currency", "null")
    fee_close = get_column_def(cols, "fee_close", "fee")
    fee_close_cost = get_column_def(cols, "fee_close_cost", "null")
    fee_close_currency = get_column_def(cols, "fee_close_currency", "null")
    open_rate_requested = get_column_def(cols, "open_rate_requested", "null")
    close_rate_requested = get_column_def(cols, "close_rate_requested", "null")
    stop_loss = get_column_def(cols, "stop_loss", "0.0")
    stop_loss_pct = get_column_def(cols, "stop_loss_pct", "null")
    initial_stop_loss = get_column_def(cols, "initial_stop_loss", "0.0")
    initial_stop_loss_pct = get_column_def(cols, "initial_stop_loss_pct", "null")
    is_stop_loss_trailing = get_column_def(
        cols,
        "is_stop_loss_trailing",
        f"coalesce({stop_loss_pct}, 0.0) <> coalesce({initial_stop_loss_pct}, 0.0)",
    )
    max_rate = get_column_def(cols, "max_rate", "0.0")
    min_rate = get_column_def(cols, "min_rate", "null")
    exit_reason = get_column_def(cols, "sell_reason", get_column_def(cols, "exit_reason", "null"))
    strategy = get_column_def(cols, "strategy", "null")
    enter_tag = get_column_def(cols, "buy_tag", get_column_def(cols, "enter_tag", "null"))
    realized_profit = get_column_def(cols, "realized_profit", "0.0")

    trading_mode = get_column_def(cols, "trading_mode", "null")

    # Leverage Properties
    leverage = get_column_def(cols, "leverage", "1.0")
    liquidation_price = get_column_def(
        cols, "liquidation_price", get_column_def(cols, "isolated_liq", "null")
    )
    # sqlite does not support literals for booleans
    if engine.name == "postgresql":
        is_short = get_column_def(cols, "is_short", "false")
    else:
        is_short = get_column_def(cols, "is_short", "0")

    # Futures Properties
    interest_rate = get_column_def(cols, "interest_rate", "0.0")
    funding_fees = get_column_def(cols, "funding_fees", "0.0")
    funding_fee_running = get_column_def(cols, "funding_fee_running", "null")
    max_stake_amount = get_column_def(cols, "max_stake_amount", "stake_amount")
    record_version = get_column_def(cols, "record_version", "1")

    # If ticker-interval existed use that, else null.
    if has_column(cols, "ticker_interval"):
        timeframe = get_column_def(cols, "timeframe", "ticker_interval")
    else:
        timeframe = get_column_def(cols, "timeframe", "null")

    open_trade_value = get_column_def(
        cols, "open_trade_value", f"amount * open_rate * (1 + {fee_open})"
    )
    close_profit_abs = get_column_def(
        cols, "close_profit_abs", f"(amount * close_rate * (1 - {fee_close})) - {open_trade_value}"
    )
    exit_order_status = get_column_def(
        cols, "exit_order_status", get_column_def(cols, "sell_order_status", "null")
    )
    amount_requested = get_column_def(cols, "amount_requested", "amount")

    amount_precision = get_column_def(cols, "amount_precision", "null")
    price_precision = get_column_def(cols, "price_precision", "null")
    precision_mode = get_column_def(cols, "precision_mode", "null")
    contract_size = get_column_def(cols, "contract_size", "null")
    precision_mode_price = get_column_def(
        cols, "precision_mode_price", get_column_def(cols, "precision_mode", "null")
    )

    # Schema migration necessary
    with engine.begin() as connection:
        connection.execute(text(f"alter table trades rename to {trade_back_name}"))

    drop_index_on_table(engine, inspector, trade_back_name)

    order_id, trade_id = get_last_sequence_ids(engine, trade_back_name, order_back_name)

    drop_orders_table(engine, order_back_name)

    # let SQLAlchemy create the schema as required
    decl_base.metadata.create_all(engine)

    # Copy data back - following the correct schema
    with engine.begin() as connection:
        connection.execute(
            text(
                f"""insert into trades
            (id, exchange, pair, base_currency, stake_currency, is_open,
            fee_open, fee_open_cost, fee_open_currency,
            fee_close, fee_close_cost, fee_close_currency, open_rate,
            open_rate_requested, close_rate, close_rate_requested, close_profit,
            stake_amount, amount, amount_requested, open_date, close_date,
            stop_loss, stop_loss_pct, initial_stop_loss, initial_stop_loss_pct,
            is_stop_loss_trailing,
            max_rate, min_rate, exit_reason, exit_order_status, strategy, enter_tag,
            timeframe, open_trade_value, close_profit_abs,
            trading_mode, leverage, liquidation_price, is_short,
            interest_rate, funding_fees, funding_fee_running, realized_profit,
            amount_precision, price_precision, precision_mode, precision_mode_price, contract_size,
            max_stake_amount, record_version
            )
        select id, lower(exchange), pair, {base_currency} base_currency,
            {stake_currency} stake_currency,
            is_open, {fee_open} fee_open, {fee_open_cost} fee_open_cost,
            {fee_open_currency} fee_open_currency, {fee_close} fee_close,
            {fee_close_cost} fee_close_cost, {fee_close_currency} fee_close_currency,
            open_rate, {open_rate_requested} open_rate_requested, close_rate,
            {close_rate_requested} close_rate_requested, close_profit,
            stake_amount, amount, {amount_requested}, open_date, close_date,
            {stop_loss} stop_loss, {stop_loss_pct} stop_loss_pct,
            {initial_stop_loss} initial_stop_loss,
            {initial_stop_loss_pct} initial_stop_loss_pct,
            {is_stop_loss_trailing} is_stop_loss_trailing,
            {max_rate} max_rate, {min_rate} min_rate,
            case when {exit_reason} = 'sell_signal' then 'exit_signal'
                 when {exit_reason} = 'custom_sell' then 'custom_exit'
                 when {exit_reason} = 'force_sell' then 'force_exit'
                 when {exit_reason} = 'emergency_sell' then 'emergency_exit'
                 else {exit_reason}
            end exit_reason,
            {exit_order_status} exit_order_status,
            {strategy} strategy, {enter_tag} enter_tag, {timeframe} timeframe,
            {open_trade_value} open_trade_value, {close_profit_abs} close_profit_abs,
            {trading_mode} trading_mode, {leverage} leverage, {liquidation_price} liquidation_price,
            {is_short} is_short, {interest_rate} interest_rate,
            {funding_fees} funding_fees, {funding_fee_running} funding_fee_running,
            {realized_profit} realized_profit,
            {amount_precision} amount_precision, {price_precision} price_precision,
            {precision_mode} precision_mode, {precision_mode_price} precision_mode_price,
            {contract_size} contract_size, {max_stake_amount} max_stake_amount,
            {record_version} record_version
            from {trade_back_name}
            """
            )
        )

    migrate_orders_table(engine, order_back_name, cols_order)
    set_sequence_ids(engine, order_id, trade_id)


def drop_orders_table(engine, table_back_name: str):
    # Drop and recreate orders table as backup
    # This drops foreign keys, too.

    with engine.begin() as connection:
        connection.execute(text(f"create table {table_back_name} as select * from orders"))
        connection.execute(text("drop table orders"))


def migrate_orders_table(engine, table_back_name: str, cols_order: list):
    ft_fee_base = get_column_def(cols_order, "ft_fee_base", "null")
    average = get_column_def(cols_order, "average", "null")
    stop_price = get_column_def(cols_order, "stop_price", "null")
    funding_fee = get_column_def(cols_order, "funding_fee", "0.0")
    ft_amount = get_column_def(cols_order, "ft_amount", "coalesce(amount, 0.0)")
    ft_price = get_column_def(cols_order, "ft_price", "coalesce(price, 0.0)")
    ft_cancel_reason = get_column_def(cols_order, "ft_cancel_reason", "null")
    ft_order_tag = get_column_def(cols_order, "ft_order_tag", "null")

    # sqlite does not support literals for booleans
    with engine.begin() as connection:
        connection.execute(
            text(
                f"""
            insert into orders (id, ft_trade_id, ft_order_side, ft_pair, ft_is_open, order_id,
            status, symbol, order_type, side, price, amount, filled, average, remaining, cost,
            stop_price, order_date, order_filled_date, order_update_date, ft_fee_base, funding_fee,
            ft_amount, ft_price, ft_cancel_reason, ft_order_tag
            )
            select id, ft_trade_id, ft_order_side, ft_pair, ft_is_open, order_id,
            status, symbol, order_type, side, price, amount, filled, {average} average, remaining,
            cost, {stop_price} stop_price, order_date, order_filled_date,
            order_update_date, {ft_fee_base} ft_fee_base, {funding_fee} funding_fee,
            {ft_amount} ft_amount, {ft_price} ft_price, {ft_cancel_reason} ft_cancel_reason,
            {ft_order_tag} ft_order_tag
            from {table_back_name}
            """
            )
        )


def migrate_pairlocks_table(decl_base, inspector, engine, pairlock_back_name: str, cols: list):
    # Schema migration necessary
    with engine.begin() as connection:
        connection.execute(text(f"alter table pairlocks rename to {pairlock_back_name}"))

    drop_index_on_table(engine, inspector, pairlock_back_name)

    side = get_column_def(cols, "side", "'*'")

    # let SQLAlchemy create the schema as required
    decl_base.metadata.create_all(engine)
    # Copy data back - following the correct schema
    with engine.begin() as connection:
        connection.execute(
            text(
                f"""insert into pairlocks
        (id, pair, side, reason, lock_time,
         lock_end_time, active)
        select id, pair, {side} side, reason, lock_time,
         lock_end_time, active
        from {pairlock_back_name}
        """
            )
        )


def set_sqlite_to_wal(engine):
    if engine.name == "sqlite" and str(engine.url) != "sqlite://":
        # Set Mode to
        with engine.begin() as connection:
            connection.execute(text("PRAGMA journal_mode=wal"))


def fix_old_dry_orders(engine):
    with engine.begin() as connection:
        # Update current dry-run Orders where
        # - stoploss order is Open (will be replaced eventually)
        # 2nd query:
        # - current Order is open
        # - current Trade is closed
        # - current Order trade_id not equal to current Trade.id
        # - current Order not stoploss

        stmt = (
            update(Order)
            .where(
                Order.ft_is_open.is_(True),
                Order.ft_order_side == "stoploss",
                Order.order_id.like("dry%"),
            )
            .values(ft_is_open=False)
        )
        connection.execute(stmt)

        # Close dry-run orders for closed trades.
        stmt = (
            update(Order)
            .where(
                Order.ft_is_open.is_(True),
                Order.ft_trade_id.not_in(select(Trade.id).where(Trade.is_open.is_(True))),
                Order.ft_order_side != "stoploss",
                Order.order_id.like("dry%"),
            )
            .values(ft_is_open=False)
        )
        connection.execute(stmt)


def fix_wrong_max_stake_amount(engine):
    """
    Fix max_stake_amount for leveraged closed trades
    This caused record_version to be bumped to 2.
    """
    with engine.begin() as connection:
        stmt = (
            update(Trade)
            .where(
                Trade.record_version < 2,
                Trade.leverage > 1,
                Trade.is_open.is_(False),
                Trade.max_stake_amount != 0,
            )
            .values(max_stake_amount=Trade.max_stake_amount / Trade.leverage, record_version=2)
        )
        connection.execute(stmt)


def check_migrate(engine: Engine, decl_base, previous_tables: list[str]) -> None:
    """
    Checks if migration is necessary and migrates if necessary
    """
    inspector = inspect(engine)

    cols_trades = inspector.get_columns("trades")
    cols_orders = inspector.get_columns("orders")
    cols_pairlocks = inspector.get_columns("pairlocks")
    tabs = get_table_names_for_table(inspector, "trades")
    table_back_name = get_backup_name(tabs, "trades_bak")
    order_tabs = get_table_names_for_table(inspector, "orders")
    order_table_bak_name = get_backup_name(order_tabs, "orders_bak")
    pairlock_tabs = get_table_names_for_table(inspector, "pairlocks")
    pairlock_table_bak_name = get_backup_name(pairlock_tabs, "pairlocks_bak")

    # Check if migration necessary
    # Migrates both trades and orders table!
    # if ('orders' not in previous_tables
    # or not has_column(cols_orders, 'funding_fee')):
    migrating = False
    if not has_column(cols_trades, "record_version"):
        # if not has_column(cols_orders, "ft_order_tag"):
        migrating = True
        logger.info(
            f"Running database migration for trades - "
            f"backup: {table_back_name}, {order_table_bak_name}"
        )
        migrate_trades_and_orders_table(
            decl_base,
            inspector,
            engine,
            table_back_name,
            cols_trades,
            order_table_bak_name,
            cols_orders,
        )

    if not has_column(cols_pairlocks, "side"):
        migrating = True
        logger.info(f"Running database migration for pairlocks - backup: {pairlock_table_bak_name}")

        migrate_pairlocks_table(
            decl_base, inspector, engine, pairlock_table_bak_name, cols_pairlocks
        )
    if "orders" not in previous_tables and "trades" in previous_tables:
        raise OperationalException(
            "Your database seems to be very old. "
            "Please update to freqtrade 2022.3 to migrate this database or "
            "start with a fresh database."
        )

    set_sqlite_to_wal(engine)
    fix_old_dry_orders(engine)
    fix_wrong_max_stake_amount(engine)

    if migrating:
        logger.info("Database migration finished.")
