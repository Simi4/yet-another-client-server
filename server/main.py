import random
import re
import secrets
import jwt
import json
from aiohttp import web
from pathlib import Path

from db import (
    init_db, try_make_db, find_or_create_account,
    add_credits_to_account, get_account_info,
    get_my_items, try_buy_item, try_sell_item)
from session import Session
from config import ServerConfig


nickname_re = re.compile(r'[a-z0-9_]{3,20}', re.I)


def check_nickname(nickname):
    return re.fullmatch(nickname_re, nickname) is not None


async def login_handle(request):
    try:
        data = await request.json()

        # unpack nickname
        nickname = data['nickname']

        # validate user-input
        if not check_nickname(nickname):
            res = {'status': 'error', 'data': 'Invalid nickname!'}
            return web.json_response(res)

        # check that the account for this nickname is present in the db,
        # if not, then create a new one
        db = request.config_dict['DB']
        account_id = await find_or_create_account(db, nickname)

        # check that there is no active session with this nickname
        if account_id in g_sessions:
            res = {'status': 'error', 'data': 'Session already exists!'}
            return web.json_response(res)
        else:
            # create session for this account
            g_sessions[account_id] = Session()

        # add credits at every login
        await add_credits_to_account(
            db, account_id, calc_credits_added_on_login())

        # get account info from the db
        account_info = await get_account_info(db, account_id)

        # create jwt with account_id as a payload
        token = get_token(account_id)

        # final response
        res = {
            'status': 'ok',
            'token': token,
            'data': account_info
        }
    except:
        import traceback
        traceback.print_exc()
        res = {'status': 'error', 'data': 'Error during login!'}
    return web.json_response(res)


async def logout_handle(request):
    try:
        data = await request.json()
        account_id = get_account_id_from_token(data['token'])
        if account_id not in g_sessions:
            res = {'status': 'error', 'data': 'Session not found!'}
        else:
            del g_sessions[account_id]
            res = {'status': 'ok'}
    except:
        import traceback
        traceback.print_exc()
        res = {'status': 'error', 'data': 'Error during logout!'}
    return web.json_response(res)


async def get_account_info_handle(request):
    try:
        data = await request.json()
        account_id = get_account_id_from_token(data['token'])
        if account_id not in g_sessions:
            res = {'status': 'error', 'data': 'Session not found!'}
            return web.json_response(res)

        # get account info from the db
        db = request.config_dict['DB']
        account_info = await get_account_info(db, account_id)

        res = {
            'status': 'ok',
            'data': account_info
        }
    except:
        import traceback
        traceback.print_exc()
        res = {'status': 'error', 'data': 'Error during getting items!'}
    return web.json_response(res)


async def get_all_items_handle(request):
    try:
        data = await request.json()
        account_id = get_account_id_from_token(data['token'])
        if account_id not in g_sessions:
            res = {'status': 'error', 'data': 'Session not found!'}
            return web.json_response(res)

        res = {
            'status': 'ok',
            'data': g_all_items
        }
    except:
        import traceback
        traceback.print_exc()
        res = {'status': 'error', 'data': 'Error during getting items!'}
    return web.json_response(res)


async def get_my_items_handle(request):
    try:
        data = await request.json()
        account_id = get_account_id_from_token(data['token'])
        if account_id not in g_sessions:
            res = {'status': 'error', 'data': 'Session not found!'}
            return web.json_response(res)

        # get items from bd
        db = request.config_dict['DB']
        items = await get_my_items(db, account_id)

        res = {
            'status': 'ok',
            'data': items
        }
    except:
        import traceback
        traceback.print_exc()
        res = {'status': 'error', 'data': 'Error during getting items!'}
    return web.json_response(res)


async def buy_item_handle(request):
    try:
        data = await request.json()
        account_id = get_account_id_from_token(data['token'])
        if account_id not in g_sessions:
            res = {'status': 'error', 'data': 'Session not found!'}
            return web.json_response(res)

        # unpack item id as str
        item_id = str(data['id'])

        # first validation, check that user-input is allowed
        if item_id not in g_all_items:
            res = {'status': 'error', 'data': 'Unknown item id to buy!'}
            return web.json_response(res)

        # get price of item
        item_price = g_all_items[item_id]['price']

        # convert to int
        item_id = int(item_id)

        # try to buy an item (all extended validation there)
        db = request.config_dict['DB']
        ok, msg = await try_buy_item(db, account_id, item_id, item_price)

        res = {
            'status': 'ok' if ok else 'error',
            'data': msg
        }
    except:
        import traceback
        traceback.print_exc()
        res = {'status': 'error', 'data': 'Error during getting items!'}
    return web.json_response(res)


async def sell_item_handle(request):
    try:
        data = await request.json()
        account_id = get_account_id_from_token(data['token'])
        if account_id not in g_sessions:
            res = {'status': 'error', 'data': 'Session not found!'}
            return web.json_response(res)

        # unpack item id as str
        item_id = str(data['id'])

        # first validation, check that user-input is allowed
        if item_id not in g_all_items:
            res = {'status': 'error', 'data': 'Unknown item id to sell!'}
            return web.json_response(res)

        # get price of item
        item_price = g_all_items[item_id]['price']

        # convert to int
        item_id = int(item_id)

        # try to sell an item (all extended validation there)
        db = request.config_dict['DB']
        ok, msg = await try_sell_item(db, account_id, item_id, item_price)

        res = {
            'status': 'ok' if ok else 'error',
            'data': msg
        }
    except:
        import traceback
        traceback.print_exc()
        res = {'status': 'error', 'data': 'Error during getting items!'}
    return web.json_response(res)


def calc_credits_added_on_login():
    return random.randint(
        g_config.credits_range_begin, g_config.credits_range_end)


def get_account_id_from_token(token):
    ''' When an invalid token is received, the exception will be raised! '''
    return jwt.decode(token, g_secret_key)['account_id']


def get_token(account_id):
    return jwt.encode(
        payload={'account_id': account_id}, key=g_secret_key).decode('utf-8')


async def init_app():
    app = web.Application()
    app.add_routes([
        web.post("/login", login_handle),
        web.post("/get_account_info", get_account_info_handle),
        web.post("/get_all_items", get_all_items_handle),
        web.post("/get_my_items", get_my_items_handle),
        web.post("/buy_item", buy_item_handle),
        web.post("/sell_item", sell_item_handle),
        web.post("/logout", logout_handle)
    ])
    app.cleanup_ctx.append(init_db)
    return app


if __name__ == '__main__':
    # load server configuration
    g_config = ServerConfig()

    # init storage for sessions (of course, dict is not perfect)
    g_sessions = {}

    # create key used for jwt
    g_secret_key = 'secret' # use this for better security: secrets.token_urlsafe(12)

    # load items from a file
    with Path('data/all_items.json').open('r', encoding='utf-8') as f:
        g_all_items = json.load(f)

    # create and fill database, if it didn't exist
    try_make_db()

    # run server
    web.run_app(init_app(), host=g_config.host, port=g_config.port)
