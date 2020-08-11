import asyncio
import selectors
import logging

from core import ClientAppCore
from ui import ClientAppUi

if __name__ == '__main__':
    # setup logger
    logging.basicConfig(filename='app.log', filemode='w',
        level=logging.INFO, format='[%(asctime)s] %(message)s')

    # fix prompt-toolkit event-loop issue
    selector = selectors.SelectSelector()
    loop = asyncio.SelectorEventLoop(selector)
    asyncio.set_event_loop(loop)

    logging.info('Client core application initialization')
    core_app = ClientAppCore()

    logging.info('Client ui application initialization')
    ui_app = ClientAppUi(core_app)
