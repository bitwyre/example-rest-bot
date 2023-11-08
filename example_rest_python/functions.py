import requests
import json
import hmac
import logging

from decimal import Decimal
from time import time_ns
from hashlib import sha256, sha512
from time import sleep
from random import choice, uniform, sample
from traceback import format_exc

from example_rest_python.config import (
    API_KEY,
    API_SECRET,
    URL_API_BITWYRE,
    URI_PUBLIC_API_BITWYRE,
    URI_PRIVATE_API_BITWYRE,
    TIMEOUT,
    SLEEP,
    OrderSide,
    OrderStatus,
)

logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)  # Set the desired logging level

# Create a console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)  # Set the desired logging level for the handler

# Create a formatter and add it to the handler
formatter = logging.Formatter('\n%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(ch)


class BitwyreRestBot:
    def __init__(
        self,
        instrument: str,
        mid_price: Decimal,
        qty: Decimal,
        price_precision: int,
        qty_precision: int,
        min_spread: Decimal,
        max_spread: Decimal,
    ):
        logger.debug("Starting BitwyreRestBot")

        # Initialize environments
        self.instrument = instrument
        self.base_asset = instrument.split("_")[0]
        self.quote_asset = instrument.split("_")[1]
        self.product = instrument.split("_")[2]
        self.api_key = API_KEY
        self.api_secret = API_SECRET
        self.timeout = TIMEOUT
        self.url = URL_API_BITWYRE
        self.uri_public = URI_PUBLIC_API_BITWYRE
        self.uri_private = URI_PRIVATE_API_BITWYRE
        self.sleep = SLEEP

        # Initialize orders
        self.open_bids = []
        self.open_asks = []
        self.closed_bids = []
        self.closed_asks = []

        # enums
        self.order_sides = [side.value for side in OrderSide]
        self.closed_status = [
            OrderStatus.DoneForToday.value,
            OrderStatus.Cancelled.value,
            OrderStatus.Replaced.value,
            OrderStatus.Stopped.value,
            OrderStatus.Rejected.value,
            OrderStatus.Suspended.value,
            OrderStatus.Expired.value,
            OrderStatus.Stopped.value,
        ]

        # configs
        self.mid_price = mid_price
        self.price_precision = price_precision
        self.qty_precision = qty_precision
        self.qty = qty
        self.min_spread = min_spread
        self.max_spread = max_spread

    def main(self):
        self.randomize_order()
        sleep(self.sleep)

        self.update_orders()
        sleep(self.sleep)

        self.random_cancel()
        sleep(self.sleep)

    def random_cancel(self):
        # delete random order to be cancelled
        order_tobe_cancelled = sample(
            self.open_bids, min(0, len(self.open_bids))
        ) + sample(self.open_asks, min(0, len(self.open_asks)))

        for order in order_tobe_cancelled:
            self.cancel_order(order_id=order["orderid"], qty="-1")  # cancel all qty

    def update_orders(self):
        updated_bids = []
        updated_asks = []
        bids_ids = [order["orderid"] for order in self.open_bids]
        bids_ask = [order["orderid"] for order in self.open_bids]

        # fetch order infos
        for order_id in bids_ids:
            success, result = self.order_info(order_id=order_id)
            if not success:
                continue
            updated_bids.append(result)

        for order_id in bids_ask:
            success, result = self.order_info(order_id=order_id)
            if not success:
                continue
            updated_asks.append(result)

        # replace order with updated ones
        for updated_order in updated_bids:
            logger.debug(f"Updating order {updated_order}")
            updated_order_id = updated_order["orderid"]
            updated_order_status = updated_order["ordstatus"]

            for index, order in enumerate(self.open_bids):
                order_id = order["orderid"]
                if (
                    order_id == updated_order_id
                    and updated_order_status not in self.closed_status
                ):
                    # Replace the order with the updated version
                    self.open_bids[index] = updated_order
                    logger.debug(
                        f"Order with orderid {updated_order_id} has been updated."
                    )
                    break
                    # Delete order if its already closed
                elif (
                    order_id == updated_order_id
                    and updated_order_status in self.closed_status
                ):
                    self.closed_bids.append(updated_order)
                    del self.open_bids[index]
                    break

        for updated_order in updated_asks:
            logger.debug(f"Updating order {updated_order}")
            updated_order_id = updated_order["orderid"]
            updated_order_status = updated_order["ordstatus"]

            for index, order in enumerate(self.open_asks):
                order_id = order["orderid"]
                if (
                    order_id == updated_order_id
                    and updated_order_status not in self.closed_status
                ):
                    # Replace the order with the updated version
                    self.open_asks[index] = updated_order
                    logger.debug(
                        f"Order with orderid {updated_order_id} has been updated."
                    )
                    break
                elif (
                    order_id == updated_order_id
                    and updated_order_status in self.closed_status
                ):
                    # Delete order if its already closed
                    del self.open_asks[index]
                    self.closed_asks.append(updated_order)
                    break

    def randomize_order(self):
        ordtype = 2  # limit order
        leverage = 1  # spot leverage is 1
        side = choice(self.order_sides)  # pick random side
        price = self.decim(round(self.mid_price, self.price_precision))
        qty = self.decim(round(self.qty, self.qty_precision))

        if len(self.open_bids + self.open_asks) == 0:
            # No open order, post original price
            return self.create_order(
                side=side,
                ordtype=ordtype,
                orderqty=str(qty),
                price=str(price),
                leverage=leverage,
            )

        self.mid_price = self.calculate_midprice()
        if side == OrderSide.Buy.value:
            price = self.mid_price * self.decim(1 - uniform(self.min_spread, self.max_spread))
        else:
            price = self.mid_price * self.decim(1 + uniform(self.min_spread, self.max_spread))

        price = self.decim(round(price, self.price_precision))
        return self.create_order(
            side=side,
            ordtype=ordtype,
            orderqty=str(qty),
            price=str(price),
            leverage=leverage,
        )

    def create_order(
        self,
        side: int,
        ordtype: int,
        orderqty: str,
        price: str = None,
        leverage: str = None,
        stoppx: str = None,
        clordid: str = None,
        timeinforce: int = None,
        expiretime: int = None,
        execinst: str = None,
    ):
        logger.debug("Inserting new order")
        uri_path = URI_PRIVATE_API_BITWYRE.get("ORDER")
        payload = {
            "instrument": self.instrument,
            "side": side,
            "ordtype": ordtype,
            "orderqty": str(orderqty),
        }

        if price is not None:
            # Non-market orders (limit, ioc, etc) require price
            payload["price"] = str(price)

        if stoppx is not None:
            payload["stoppx"] = stoppx
        if clordid is not None:
            payload["clordid"] = clordid
        if timeinforce is not None:
            payload["timeinforce"] = timeinforce
        if expiretime is not None:
            payload["expiretime"] = expiretime
        if execinst is not None:
            payload["execinst"] = execinst

        if self.product == "futures":
            # Futures product requires leverage
            payload["leverage"] = int(leverage)
        else:
            # Spot product leverage is alwaus 1
            payload["leverage"] = int(leverage)

        payload = json.dumps(payload)

        (nonce, checksum, signature) = self.sign(self.api_secret, uri_path, payload)
        headers = {
            "API-Key": self.api_key,
            "API-Sign": signature,
        }

        data = {"nonce": nonce, "checksum": checksum, "payload": payload}
        url = self.url + uri_path

        logger.debug(f"Sending {data} to {url} with headers {headers}")
        (success, result) = self.post(url, headers, data, self.timeout)

        if not success:
            logger.error("Failed in posting order")
            return
        result = result["result"]
        """
        Exec report sample
        {
            "AvgPx": "0",
            "LastLiquidityInd": "0",
            "LastPx": "0",
            "LastQty": "0",
            "account": "a9e3d010-3169-489d-9063-ced912b0fdc8",
            "cancelondisconnect": 0,
            "clorderid": "",
            "cumqty": "0",
            "execid": "",
            "exectype": 0,
            "expiry": 0,
            "fill_price": "0",
            "instrument": "btc_usdt_spot",
            "leavesqty": "2.9301",
            "orderid": "a9e3d010-3169-489d-9063-ced912b0fdc9",
            "orderqty": "2.9301",
            "ordrejreason": "",
            "ordstatus": 0,
            "ordstatusReqID": "a9e3d010-3169-489d-9063-ced912b0fdc9",
            "ordtype": 1,
            "origclid": "a9e3d010-3169-489d-9063-ced912b0fdc9",
            "price": "10.0",
            "side": 2,
            "stoppx": "0",
            "time_in_force": 0,
            "timestamp": 123123132123,
            "transacttime": 0,
            "value": "100.0"
        }
        """
        if result["ordstatus"] in [0, 1, 11, 13]:
            # New, partial fill, calculating, open orders
            if side == 1:
                self.open_bids.append(result)
            elif side == 2:
                self.open_asks.append(result)
        else:
            # closed orders
            if side == 1:
                self.closed_bids.append(result)
            elif side == 2:
                self.closed_asks.append(result)
        return

    def order_info(
        self,
        order_id: str,
    ):
        success: bool = False
        result: dict = {}
        logger.debug(f"Gettiing info order {order_id}")
        uri_path = URI_PRIVATE_API_BITWYRE.get("ORDER_INFO") +  "/" + order_id
        payload = ""
        (nonce, checksum, signature) = self.sign(
            self.api_secret, uri_path, payload
        )

        headers = {"API-Key": self.api_key, "API-Sign": signature}
        params = {"nonce": nonce, "checksum": checksum, "payload": payload}
        url = self.url + uri_path

        logger.debug(f"Sending {params} to {url} with headers {headers}")
        success, result = self.get(url, headers, params, self.timeout)

        if not success:
            logger.error("Failed in getting order info")
            return (success, result)
        
        result = result["result"][0]
        return (success, result)

    def cancel_order(self, order_id: str, qty: str):
        success: bool = False
        result: dict = {}
        logger.debug(f"Cancelling order {order_id} qty {qty}")

        uri_path = URI_PRIVATE_API_BITWYRE.get("CANCEL_ORDER")
        payload = {"order_ids": [order_id], "qtys": [qty]}
        payload = json.dumps(payload)

        (nonce, checksum, signature) = self.sign(self.api_secret, uri_path, payload)
        headers = {"API-Key": self.api_key, "API-Sign": signature}
        params = {"nonce": nonce, "checksum": checksum, "payload": payload}
        url = self.url + uri_path

        logger.debug(f"Sending {params} to {url} with headers {headers}")
        success, result = self.delete(url, headers, params, self.timeout)

        if not success:
            logger.error("Failed in cancelling")
            return (success, result)

        return (success, result)

    @staticmethod
    def get(url: str, headers: dict, params: dict, timeout: int):
        success: bool = False
        response: requests.Response = None
        status_code: int = 500
        result: dict = {}
        error: dict = []

        try:
            response = requests.get(
                url=url,
                headers=headers,
                params=params,
                timeout=timeout,
            )
        except requests.exceptions.Timeout as e:
            logger.error(
                f"Error Timeout in getting {params} to {url} with headers {headers}"
            )
            logger.error(e)
            return (success, result)
        except requests.exceptions.ConnectionError as e:
            logger.error(
                f"Error Connection error in getting {params} to {url} with headers {headers}"
            )
            logger.error(e)
            return (success, result)
        except Exception as e:
            logger.error(
                f"Exception {e} in getting {params} to {url} with headers {headers}"
            )
            logger.error(e)
            logger.error(format_exc())
            return (success, result)
        try:
            result = response.json()
        except Exception as e:
            logger.error(
                f"Exception {e} failed in parsing getting {params}, raw response {response.text}"
            )
            logger.error(format_exc())
            return (success, result)

        status_code = int(response.status_code)
        logger.debug(f"Raw response {result}")
        error = result["error"]
        if len(error) != 0 or status_code != 200:
            logger.error(f"Failed in getting {params} to {url} with headers {headers}")
            logger.error(f"Status code {status_code}, error message {error}")
            return (success, result)

        logger.debug(f"Success fetching data, result {result}")
        success = True
        return (success, result)

    @staticmethod
    def post(url: str, headers: dict, data: dict, timeout: int):
        success: bool = False
        response: requests.Response = None
        status_code: int = 500
        result: dict = []
        error: dict = []

        try:
            response = requests.post(
                url=url, headers=headers, data=data, timeout=timeout
            )
        except requests.exceptions.Timeout as e:
            logger.error(
                f"Error Timeout in posting {data} to {url} with headers {headers}"
            )
            logger.error(e)
            return (success, result)
        except requests.exceptions.ConnectionError as e:
            logger.error(
                f"Error Connection error in posting {data} to {url} with headers {headers}"
            )
            logger.error(e)
            return (success, result)
        except Exception as e:
            logger.error(
                f"Exception error in posting {data} to {url} with headers {headers}"
            )
            logger.error(e)
            logger.error(format_exc())
            return (success, result)

        try:
            result = response.json()
        except Exception as e:
            logger.error(
                f"Exception {e} in parsing posting {data}, raw response {response.text}"
            )
            logger.error(format_exc())
            return (success, result)

        status_code = int(response.status_code)
        error = result["error"]
        if len(error) != 0 or status_code != 200:
            logger.error(f"Failed in posting {data} to {url} with headers {headers}")
            logger.error(f"Status code {status_code}, error message {error}")
            return (success, result)

        logger.debug(f"Success posting data, result {result}")
        success = True
        return (success, result)

    def delete(url: str, headers: dict, params: dict, timeout: int):
        success: bool = False
        response: requests.Response = None
        status_code: int = 500
        result: dict = {}
        error: dict = []

        try:
            response = requests.get(
                url - url,
                headers=headers,
                params=params,
                timeout=timeout,
            )
        except requests.exceptions.Timeout as e:
            logger.error(
                f"Error Timeout in getting {params} to {url} with headers {headers}"
            )
            logger.error(e)
            return (success, result)
        except requests.exceptions.ConnectionError as e:
            logger.error(
                f"Error Connection error in getting {params} to {url} with headers {headers}"
            )
            logger.error(e)
            return (success, result)
        except Exception as e:
            logger.error(
                f"Exception error in getting {params} to {url} with headers {headers}"
            )
            logger.error(e)
            logger.error(format_exc())
            return (success, result)
        try:
            result = response.json()
        except Exception as e:
            logger.error(
                f"Exception {e} in parsing getting {params}, raw response {response.text}"
            )
            logger.error(format_exc())
            return (success, result)

        status_code = int(response.status_code)
        error = result["error"]
        if len(error) != 0 or status_code != 200:
            logger.error(f"Failed in getting {params} to {url} with headers {headers}")
            logger.error(f"Status code {status_code}, error message {error}")
            return (success, result)

        logger.debug(f"Success fetching data, result {result}")
        success = True
        return (success, result)

    def calculate_midprice(self) -> Decimal:
        midprice: Decimal = None
        if len(self.open_bids) > 0 and len(self.open_asks) > 0:
            best_bid = max(float(buy_order["price"]) for buy_order in self.open_bids)
            best_ask = min(float(sell_order["price"]) for sell_order in self.open_asks)
            midprice = self.decim((best_bid + best_ask) / 2)
        elif len(self.open_bids) > 0 and len(self.open_asks) == 0:
            midprice = self.decim(
                max(float(buy_order["price"]) for buy_order in self.open_bids)
            )
        elif len(self.open_asks) > 0 and len(self.open_bids) == 0:
            midprice = self.decim(
                min(float(sell_order["price"]) for sell_order in self.open_asks)
            )
        else:
            midprice = self.decim(self.mid_price)
        return midprice

    @staticmethod
    def sign(secret_key: str, uri_path: str, payload: str) -> (int, str, str):
        nonce = time_ns()
        payload = json.dumps(payload)
        payload = json.dumps(payload)
        checksum = sha256(str(payload).encode("utf-8")).hexdigest()
        nonce_checksum = sha256(
            str(nonce).encode("utf-8") + str(checksum).encode("utf-8")
        ).hexdigest()
        signature = hmac.new(
            secret_key.encode("utf-8"),
            uri_path.encode("utf-8") + nonce_checksum.encode("utf-8"),
            sha512,
        ).hexdigest()
        return (nonce, checksum, signature)

    @staticmethod
    def decim(num):
        return Decimal(str(num))
