import graphene
from .types import *
from .types.address import AddressQuery
from .types.analytics import AnalyticsQuery
from .types.basket import BasketQuery
from .types.catalogue import CatalogueQuery
from .types.communication import CommunicationQuery
from .types.customer import CustomerQuery
from .types.offer import OfferQuery
from .types.order import OrderQuery
from .types.partner import PartnerQuery
from .types.payment import PaymentQuery
from .types.shipping import ShippingQuery
from .types.voucher import VoucherQuery
from .types.wishlists import WishListQuery

# Combine all queries into a single root query class
class Query(
    AddressQuery,
    AnalyticsQuery,
    BasketQuery,
    CatalogueQuery,
    CommunicationQuery,
    CustomerQuery,
    OfferQuery,
    OrderQuery,
    PartnerQuery,
    PaymentQuery,
    ShippingQuery,
    VoucherQuery,
    WishListQuery,
    graphene.ObjectType,  # Base class for all queries
):
    pass