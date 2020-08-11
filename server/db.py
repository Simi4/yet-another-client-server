import aiosqlite
import sqlite3
from pathlib import Path


sqlite_db = Path('db.sqlite3')


async def init_db(app):
    db = await aiosqlite.connect(sqlite_db)
    db.row_factory = aiosqlite.Row
    app['DB'] = db
    yield
    await db.close()


def try_make_db():
    if sqlite_db.exists():
        return

    with sqlite3.connect(sqlite_db) as conn:
        cur = conn.cursor()
        cur.execute(
            '''CREATE TABLE IF NOT EXISTS Accounts (
            nickname TEXT NOT NULL,
            credits INTEGER DEFAULT 0)
            '''
        )
        cur.execute(
            '''CREATE TABLE IF NOT EXISTS Items (
            account_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL)
            '''
        )
        conn.commit()


async def find_or_create_account(db, nickname):
    async with db.execute(
        'SELECT rowid FROM Accounts WHERE nickname = ? COLLATE NOCASE', [nickname]
    ) as cursor:
        row = await cursor.fetchone()
        if row is not None:
            return row['rowid']
    async with db.execute('INSERT INTO Accounts (nickname) VALUES (?)', [nickname]) as cursor:
        # sqlite doesn't support a RETURNING sql-keyword, using lastrowid instead
        account_id = cursor.lastrowid
    await db.commit()
    return account_id


async def add_credits_to_account(db, account_id, amount_of_credits):
    await db.execute(
        'UPDATE Accounts SET credits = credits + ? WHERE rowid = ?', [amount_of_credits, account_id])
    await db.commit()


async def try_buy_item(db, account_id, item_id, item_price):
    # check that item was not already purchased
    async with db.execute(
        'SELECT rowid FROM Items WHERE account_id = ? AND item_id = ?', [account_id, item_id]
    ) as cursor:
        row = await cursor.fetchone()
        if row is not None:
            return False, 'Item was already purchased!'

    # check that there are enough credits for the purchase
    async with db.execute(
        'SELECT credits FROM Accounts WHERE rowid = ?', [account_id]
    ) as cursor:
        row = await cursor.fetchone()
        credits = int(row['credits'])
    if credits < item_price:
        return False, 'Not enough credits to buy item!'

    await db.execute(
        'UPDATE Accounts SET credits = credits - ? WHERE rowid = ?', [item_price, account_id])
    await db.execute('INSERT INTO Items (account_id, item_id) VALUES (?, ?)', [account_id, item_id])
    await db.commit()

    return True, 'Item was purchased successfully.'


async def try_sell_item(db, account_id, item_id, item_price):
    # check that item was not already purchased
    async with db.execute(
        'SELECT rowid FROM Items WHERE account_id = ? AND item_id = ?', [account_id, item_id]
    ) as cursor:
        row = await cursor.fetchone()
        if row is None:
            return False, 'There is no such item in account!'
        rowid = row['rowid']

    await db.execute('DELETE FROM Items WHERE rowid = ?', [rowid])
    await db.execute(
        'UPDATE Accounts SET credits = credits + ? WHERE rowid = ?', [item_price, account_id])
    await db.commit()

    return True, 'Item was sold successfully.'


async def get_my_items(db, account_id):
    items = []
    async with db.execute(
        'SELECT item_id FROM Items WHERE account_id = ?', [account_id]
    ) as cursor:
        records = await cursor.fetchall()
        for row in records:
            items.append(row['item_id'])
    return items


async def get_account_info(db, account_id):
    # no checks there
    async with db.execute('SELECT * FROM Accounts WHERE rowid = ?', [account_id]) as cursor:
        row = await cursor.fetchone()
        nickname = row['nickname']
        credits = row['credits']
        return {
            'nickname': nickname,
            'credits': credits
        }
