from prompt_toolkit import prompt, HTML
from prompt_toolkit.validation import Validator
from prompt_toolkit.shortcuts import *


class ClientAppUi:

    def __init__(self, core_app):
        self.core_app = core_app

        # init item-id input validator
        self.item_id_validator = Validator.from_callable(
            lambda input: input.isdigit() or input == 'q',
            error_message='Введен невалидный номер предмета!\n' \
                'Проверьте правильность введенных данных.',
            move_cursor_to_end=True
        )
        # clear screen
        clear()

        # welcome message, show on app start
        message_dialog(
            title='Добро пожаловать!',
            text='Вас приветствует консольное приложение,\n' \
                'реализующеее упрощенную модель экономики игры WoWS.\n' \
                'Нажмите Enter чтобы продолжить.'
        ).run()

        # switch to login interface
        self.login_interface()

    def login_interface(self):
        while True:
            nickname = input_dialog(
                title='Вход',
                text='Введите свой никнейм:'
            ).run()

            if nickname is None:
                return

            if not self.core_app.check_nickname(nickname):
                message_dialog(
                    title='Введен невалидный никнейм!',
                    text='Проверьте правильность введенных данных.'
                ).run()
                continue

            # attempt to login with nickname
            ok, result = self.core_app.login(nickname)

            if ok:
                # switch to game session interface
                self.game_session_interface()

            else:
                message_dialog(
                    title='Ошибка входа!',
                    text=f'Ошибка: {result}'
                ).run()

    def game_session_interface(self):
        while True:
            result = button_dialog(
                title='Выберите действие',
                text='info:      Просмотр информации аккаунта (никнейм и количество кредитов)\n' \
                    'all items: Полный список всевозможного имущества\n' \
                    'my items:  Просмотр имеющегося на аккаунте имущества\n' \
                    'buy item:  Покупка имущества\n' \
                    'sell item: Продажа имущества\n' \
                    'logout:    Выход из аккаунта',
                buttons=[
                    ('info', 1),
                    ('all items', 2),
                    ('my items', 3),
                    ('buy item', 4),
                    ('sell item', 5),
                    ('logout', 6)
                ],
            ).run()

            clear()

            if result == 1:
                self.show_account_info()

            elif result == 2:
                self.show_all_items()

            elif result == 3:
                self.show_my_items()

            elif result == 4:
                self.buy_item()

            elif result == 5:
                self.sell_item()

            elif result == 6:
                self.core_app.logout()
                clear()
                # switch back to login interface
                return

            prompt('Нажмите Enter чтобы выбрать действие')

    def show_account_info(self):
        nickname = self.core_app.account_info['nickname']
        credits = self.core_app.account_info['credits']
        print_formatted_text(HTML(f'Мой никнейм: <b>{nickname}</b>'))
        print_formatted_text(HTML(f'Мои кредиты: <b>{credits}</b>'))
        print_formatted_text('')

    def show_all_items(self):
        ok, result = self.core_app.get_all_items()
        if not ok:
            print_formatted_text(f'Ошибка получения данных.\n{result}\n')
            return

        print_formatted_text('Полный список всевозможного имущества\n')

        for value in result.values():
            name = value['name']
            type = value['type']
            price = value['price']

            print_formatted_text(HTML(
                f'Название: {name}\n' \
                f'Тип: {type}\n' \
                f'Стоимость: {price}\n'
            ))

    def show_my_items(self):
        ok, result_all_items = self.core_app.get_all_items()
        if not ok:
            print_formatted_text(f'Ошибка получения данных.\n{result}\n')
            return

        ok, result_my_items = self.core_app.get_my_items()
        if not ok:
            print_formatted_text(f'Ошибка получения данных.\n{result_my_items}\n')
            return

        print_formatted_text('Моё имущество\n')

        if not result_my_items:
            print_formatted_text('Нет имущества на аккаунте\n')
            return

        for id in result_my_items:
            value = result_all_items[str(id)]
            name = value['name']
            type = value['type']
            price = value['price']

            print_formatted_text(HTML(
                f'Название: {name}\n' \
                f'Тип: {type}\n' \
                f'Стоимость: {price}\n'
            ))

    def buy_item(self):
        ok, result_all_items = self.core_app.get_all_items()
        if not ok:
            print_formatted_text(f'Ошибка получения данных.\n{result_all_items}\n')
            return

        ok, result_my_items = self.core_app.get_my_items()
        if not ok:
            print_formatted_text(f'Ошибка получения данных.\n{result_my_items}\n')
            return

        my_credits = self.core_app.account_info['credits']
        print_formatted_text('Покупка имущества (отображено имущество доступное к покупке)')
        print_formatted_text(f'Мои кредиты: {my_credits}\n')

        if len(result_all_items) == len(result_my_items):
            print_formatted_text('Вы уже владеете всем имуществом.\n')
            return

        allowed_ids = []
        for id, value in result_all_items.items():
            name = value['name']
            type = value['type']
            price = value['price']

            # skip already purchased items
            if int(id) in result_my_items:
                continue

            # skip expensive items
            if my_credits < price:
                continue

            allowed_ids.append(id)
            print_formatted_text(HTML(
                f'Номер: {id}\n' \
                f'Название: {name}\n' \
                f'Тип: {type}\n' \
                f'Стоимость покупки: {price}\n'
            ))

        if not allowed_ids:
            print_formatted_text(
                'Нет имущества доступного к покупке, попробуйте заработать больше кредитов!\n')
            return

        while True:
            input = prompt(
                'Введите номер имущества, которое хотите приобрести, или q для выхода: ',
                validator=self.item_id_validator,
                validate_while_typing=True
            )

            if input == 'q':
                clear()
                return

            # input-validation
            if input not in allowed_ids:
                print_formatted_text('Введен недопустимый номер имущества.\n')
                continue

            # buy-request to server
            ok, result = self.core_app.buy_item(input)
            if not ok:
                print_formatted_text(f'Ошибка при совершении покупки.\n{result}\n')
                continue

            else:
                clear()
                print_formatted_text('Покупка успешно совершена!\n')
                return

    def sell_item(self):
        ok, result_all_items = self.core_app.get_all_items()
        if not ok:
            print_formatted_text(f'Ошибка получения данных.\n{result_all_items}\n')
            return

        ok, result_my_items = self.core_app.get_my_items()
        if not ok:
            print_formatted_text(f'Ошибка получения данных.\n{result_my_items}\n')
            return

        print_formatted_text('Продажа имущества (отображено имущество доступное для продажи)\n')

        if not result_my_items:
            print_formatted_text('Нет имущества для продажи.\n')
            return

        for id in result_my_items:
            value = result_all_items[str(id)]
            name = value['name']
            type = value['type']
            price = value['price']

            print_formatted_text(HTML(
                f'Номер: {id}\n' \
                f'Название: {name}\n' \
                f'Тип: {type}\n' \
                f'Стоимость продажи: {price}\n'
            ))

        while True:
            input = prompt(
                'Введите номер имущества, которое хотите продать, или q для выхода: ',
                validator=self.item_id_validator,
                validate_while_typing=True
            )

            if input == 'q':
                clear()
                return

            # input-validation
            if int(input) not in result_my_items:
                print_formatted_text('Введен недопустимый номер имущества.\n')
                continue

            # sell-request to server
            ok, result = self.core_app.sell_item(input)
            if not ok:
                print_formatted_text(f'Ошибка при совершении продажи.\n{result}\n')
                continue

            else:
                clear()
                print_formatted_text('Продажа успешно совершена!\n')
                return
