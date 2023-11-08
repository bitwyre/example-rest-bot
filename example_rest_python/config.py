from enum import Enum

API_KEY = "lorem"
API_SECRET = "ipsum"

URL_API_BITWYRE = "https://api.bitwyre.com"
URI_PUBLIC_API_BITWYRE = {
    "SERVERTIME": "/public/time",
    "TRADES": "/public/trades",
    "TICKER": "/public/ticker",
    "INSTRUMENT": "/public/pairs",
    "DEPTH": "/public/depth",
    "ANNOUNCEMENTS": "/public/announcements",
    "PRODUCTS": "/public/products",
    "MARKETS": "/public/markets",
    "ASSETS": "/public/assets",
    "THROUGHPUT": "/public/throughput",
    "DERIVATIVE_INFO": "/public/derivatives/info",
    "DERIVATIVE_MARK_PRICE": "/public/derivatives/mark-price",
}
URI_PRIVATE_API_BITWYRE = {
    "ACCOUNT_BALANCE": "/private/account/spotbalance",
    "ACCOUNT_BALANCE_MEM": "/private/account/spotbalance/inmemory",
    "ACCOUNT_STATEMENT": "/private/account/statement",
    "DERIVATIVE_ACCOUNT_BALANCE": "/private/derivatives/account",
    "TRANSACTION_HISTORIES": "/private/account/transactions",
    "ORDER": "/private/orders",
    "CANCEL_ORDER": "/private/orders/cancel",
    "OPEN_ORDERS": "/private/orders/open",
    "CLOSED_ORDERS": "/private/orders/closed",
    "ORDER_INFO": "/private/orders/info",
    "ORDER_INFO_MEM": "/private/orders/info/inmemory",
    "TRADE_HISTORY": "/private/trades",
    "ORDER_JOURNEY": "/private/orders/journey",
    "ORDER_HISTORY": "/private/orders/histories"
}

TIMEOUT = 5
SLEEP = 5

class OrderSide(Enum):
    Buy = 1
    Sell = 2

class OrderType(Enum):
    Market = 1
    Limit = 2
    Stop = 3
    Stop_Limit = 4
    Post_Only = 19
    IOC = 20
    Limit_IOC = 21
    FOK = 22
    
class OrderStatus(Enum):
    New = 0
    PartiallyFilled = 1
    Filled = 2
    DoneForToday = 3
    Cancelled = 4
    Replaced = 5
    PendingCancel = 6
    Stopped = 7
    Rejected = 8
    Suspended = 9
    PendingNew = 10
    Calculated = 11
    Expired = 12
    AcceptedForBidding = 13
    PendingReplace = 14
    PendingExpire = 15
    PartialCancel = 16
    PartialCancelTooBig = 17
    PendingPartialCancel = 18
    PendingSuspend = 19

class OrderRejectReason(Enum):
    BrokerExchangeOption = 0
    UnknownSymbol = 1
    ExchangeClosed = 2
    OrderExceedsLimit = 3
    TooLateToEnter = 4
    UnknownOrder = 5
    DuplicateOrder = 6
    DuplicateVerballyCommunicatedOrder = 7
    StaleOrder = 8
    TradeAlongRequired = 9
    InvalidInvestorID = 10
    UnsupportedOrderCharacteristic = 11
    SurveillanceOption = 12
    IncorrectQuantity = 13
    IncorrectAllocatedQuantity = 14
    UnknownAccounts = 15
    PriceExceedsCurrentPriceBand = 16
    InvalidPriceIncrement = 17
    ReferencePriceNotAvailable = 19  # for derivatives
    NotionalValueExceedsThreshold = 20
    AlgorithmRiskThresholdBreached = 21
    ShortSellNotPermitted = 22
    ShortSellRejectedSecurityPreBorrowRestrictions = 23
    ShortSellRejectedAccountPreBorrowRestrictions = 24
    InsufficientCreditLimit = 25
    ExceededClipSizeLimit = 26
    ExceededMaxNotionalOrderAmount = 27
    ExceededDV01Limit = 28
    ExceededCS01Limit = 29
    SelfMatch = 30
    NegativeBalance = 31
    Mallicious = 32
    Other = 99
    Nothing = 100


class ExecType(Enum):
    New = 0
    Trade = 2
    Done_for_day = 3
    Canceled = 4
    Replace = 5
    Pending_cancel = 6
    Stopped = 7
    Rejected = 8
    Suspended = 9
    Pending_New = 10
    Calculated = 11
    Expired = 12
    Restated = 13
    Pending_Replace = 14
    Trade_Correct = 16
    Trade_Cancel = 17
    Order_Status = 18
    
