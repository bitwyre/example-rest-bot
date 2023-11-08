from example_rest_python.functions import BitwyreRestBot
from time import sleep
def cli():
    bot = BitwyreRestBot(
        instrument="btc_usdt_spot",
        mid_price=30000,
        qty=0.5,
        price_precision=2,
        qty_precision=2,
        min_spread=0,
        max_spread=0.01,
    )
    while True:
        bot.main()