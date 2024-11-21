import graphene
from .types.address import AddressMutation
from .types.analytics import AnalyticsMutation
from .types.basket import BasketMutation
from .types.catalogue import CatalogueMutation
from .types.communication import CommunicationMutation
from .types.customer import CustomerMutation
from .types.offer import OfferMutation
from .types.order import OrderMutation
from .types.partner import PartnerMutation
from .types.payment import PaymentMutation
from .types.shipping import ShippingMutation
from .types.voucher import VoucherMutation
from .types.wishlists import WishListMutation

class Mutation(
    AddressMutation,
    AnalyticsMutation,
    BasketMutation,
    CatalogueMutation,
    CommunicationMutation,
    CustomerMutation,
    OfferMutation,
    OrderMutation,
    PartnerMutation,
    PaymentMutation,
    ShippingMutation,
    VoucherMutation,
    WishListMutation,
    graphene.ObjectType,
):
    pass