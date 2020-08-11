import logging
import requests
import re

from config import AppConfig


class ClientAppCore:

    def __init__(self):
        self.config = AppConfig()
        self.session = requests.Session()

    def request_with_token(self, name, data = {}):
        url = f'http://{self.config.host}:{self.config.port}/{name}'
        try:
            # extend data with token
            data['token'] = self.token
            resp = self.session.post(url, json=data, timeout=3)
            data = resp.json()
            if data['status'] == 'ok':
                return True, data['data']
            else:
                return False, data['data']
        except Exception as e:
            logging.info(e)
            return False, 'Error during getting data!'

    def get_all_items(self):
        # return cached items, if present
        if hasattr(self, 'all_items'):
            return True, self.all_items

        ok, result = self.request_with_token('get_all_items')

        if ok:
            # cache items
            self.all_items = result

        return ok, result

    def get_my_items(self):
        return self.request_with_token('get_my_items')

    def buy_item(self, item_id):
        ok, result = self.request_with_token('buy_item', {'id': item_id})

        if ok:
            self.invalidate_account_info()

        return ok, result

    def sell_item(self, item_id):
        ok, result = self.request_with_token('sell_item', {'id': item_id})

        if ok:
            self.invalidate_account_info()

        return ok, result

    def invalidate_account_info(self):
        ok, result = self.request_with_token('get_account_info')

        if not ok:
            return

        # update data
        self.account_info = result

    def login(self, nickname):
        login_url = f'http://{self.config.host}:{self.config.port}/login'
        try:
            data = {'nickname': nickname}
            resp = self.session.post(login_url, json=data, timeout=3)
            data = resp.json()
            if data['status'] == 'ok':
                # store token
                self.token = data['token']

                # store account data
                self.account_info = data['data']
                return True, self.account_info
            else:
                return False, data['data']
        except Exception as e:
            logging.info(e)
            return False, 'Error during login'

    def logout(self):
        logout_url = f'http://{self.config.host}:{self.config.port}/logout'
        try:
            data = {'token': self.token}
            resp = self.session.post(logout_url, json=data, timeout=3)
        except Exception as e:
            logging.info(e)
        self.token = None

    @staticmethod
    def check_nickname(nickname):
        return re.fullmatch('[a-z0-9_]{3,20}', nickname, re.I) is not None
