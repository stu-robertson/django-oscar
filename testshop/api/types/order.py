from graphene import relay
from graphene_django import DjangoObjectType
import graphene
from oscar.apps.order.models import (
    Order,
    Line,
    OrderNote,
    OrderStatusChange,
    ShippingAddress,
    BillingAddress,
    OrderDiscount,
    LinePrice,
    ShippingEvent,
    PaymentEvent,
    Surcharge,
)


# GraphQL Types
class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = (
            "id",
            "number",
            "site",
            "user",
            "billing_address",
            "shipping_address",
            "total_incl_tax",
            "total_excl_tax",
            "shipping_incl_tax",
            "shipping_excl_tax",
            "currency",
            "status",
            "date_placed",
            "lines",
        )
        interfaces = (relay.Node,)


class OrderConnection(relay.Connection):
    class Meta:
        node = OrderType


class LineType(DjangoObjectType):
    class Meta:
        model = Line
        fields = (
            "id",
            "order",
            "product",
            "quantity",
            "line_price_incl_tax",
            "line_price_excl_tax",
            "unit_price_incl_tax",
            "unit_price_excl_tax",
            "status",
        )
        interfaces = (relay.Node,)


class LineConnection(relay.Connection):
    class Meta:
        node = LineType


class OrderNoteType(DjangoObjectType):
    class Meta:
        model = OrderNote
        fields = ("id", "order", "user", "note_type", "message", "date_created")
        interfaces = (relay.Node,)


class OrderNoteConnection(relay.Connection):
    class Meta:
        node = OrderNoteType


class OrderStatusChangeType(DjangoObjectType):
    class Meta:
        model = OrderStatusChange
        fields = ("id", "order", "old_status", "new_status", "date_created")
        interfaces = (relay.Node,)


class OrderStatusChangeConnection(relay.Connection):
    class Meta:
        node = OrderStatusChangeType


class ShippingAddressType(DjangoObjectType):
    class Meta:
        model = ShippingAddress
        fields = ("id", "line1", "line2", "city", "postcode", "country")
        interfaces = (relay.Node,)


class ShippingAddressConnection(relay.Connection):
    class Meta:
        node = ShippingAddressType


class BillingAddressType(DjangoObjectType):
    class Meta:
        model = BillingAddress
        fields = ("id", "line1", "line2", "city", "postcode", "country")
        interfaces = (relay.Node,)


class BillingAddressConnection(relay.Connection):
    class Meta:
        node = BillingAddressType


class OrderDiscountType(DjangoObjectType):
    class Meta:
        model = OrderDiscount
        fields = ("id", "order", "offer_name", "voucher_code", "amount", "category")
        interfaces = (relay.Node,)


class OrderDiscountConnection(relay.Connection):
    class Meta:
        node = OrderDiscountType


class LinePriceType(DjangoObjectType):
    class Meta:
        model = LinePrice
        fields = (
            "id",
            "line",
            "quantity",
            "price_incl_tax",
            "price_excl_tax",
            "shipping_incl_tax",
            "shipping_excl_tax",
        )
        interfaces = (relay.Node,)


class LinePriceConnection(relay.Connection):
    class Meta:
        node = LinePriceType


class ShippingEventType(DjangoObjectType):
    class Meta:
        model = ShippingEvent
        fields = ("id", "order", "lines", "event_type", "date_created")
        interfaces = (relay.Node,)


class ShippingEventConnection(relay.Connection):
    class Meta:
        node = ShippingEventType


class PaymentEventType(DjangoObjectType):
    class Meta:
        model = PaymentEvent
        fields = ("id", "order", "amount", "reference", "event_type", "date_created")
        interfaces = (relay.Node,)


class PaymentEventConnection(relay.Connection):
    class Meta:
        node = PaymentEventType


class SurchargeType(DjangoObjectType):
    class Meta:
        model = Surcharge
        fields = ("id", "order", "name", "incl_tax", "excl_tax")
        interfaces = (relay.Node,)


class SurchargeConnection(relay.Connection):
    class Meta:
        node = SurchargeType


# Queries
class OrderQuery(graphene.ObjectType):
    orders = relay.ConnectionField(OrderConnection)
    order = relay.Node.Field(OrderType)
    order_lines = relay.ConnectionField(LineConnection)
    line = relay.Node.Field(LineType)
    shipping_addresses = relay.ConnectionField(ShippingAddressConnection)
    billing_addresses = relay.ConnectionField(BillingAddressConnection)
    order_notes = relay.ConnectionField(OrderNoteConnection)
    discounts = relay.ConnectionField(OrderDiscountConnection)

    def resolve_orders(self, info, **kwargs):
        return Order.objects.all()

    def resolve_order_lines(self, info, **kwargs):
        return Line.objects.all()

    def resolve_shipping_addresses(self, info, **kwargs):
        return ShippingAddress.objects.all()

    def resolve_billing_addresses(self, info, **kwargs):
        return BillingAddress.objects.all()

    def resolve_order_notes(self, info, **kwargs):
        return OrderNote.objects.all()

    def resolve_discounts(self, info, **kwargs):
        return OrderDiscount.objects.all()


# Mutations for Order
class CreateOrderMutation(relay.ClientIDMutation):
    class Input:
        user_id = graphene.ID(required=True)
        billing_address_id = graphene.ID(required=True)
        shipping_address_id = graphene.ID(required=True)
        total_incl_tax = graphene.Float(required=True)
        total_excl_tax = graphene.Float(required=True)
        shipping_incl_tax = graphene.Float(required=True)
        shipping_excl_tax = graphene.Float(required=True)
        currency = graphene.String(required=True)
        status = graphene.String()

    order = graphene.Field(OrderType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, user_id, billing_address_id, shipping_address_id,
                                total_incl_tax, total_excl_tax, shipping_incl_tax, shipping_excl_tax,
                                currency, status=None):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
            billing_address = BillingAddress.objects.get(id=billing_address_id)
            shipping_address = ShippingAddress.objects.get(id=shipping_address_id)
        except (User.DoesNotExist, BillingAddress.DoesNotExist, ShippingAddress.DoesNotExist):
            raise Exception("Invalid user or address IDs")

        order = Order.objects.create(
            user=user,
            billing_address=billing_address,
            shipping_address=shipping_address,
            total_incl_tax=total_incl_tax,
            total_excl_tax=total_excl_tax,
            shipping_incl_tax=shipping_incl_tax,
            shipping_excl_tax=shipping_excl_tax,
            currency=currency,
            status=status or "Pending",
        )
        return CreateOrderMutation(order=order)


class UpdateOrderStatusMutation(relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)
        status = graphene.String(required=True)

    order = graphene.Field(OrderType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, id, status):
        try:
            order = Order.objects.get(id=id)
            order.status = status
            order.save()
            return UpdateOrderStatusMutation(order=order)
        except Order.DoesNotExist:
            raise Exception("Order not found")


class AddOrderNoteMutation(relay.ClientIDMutation):
    class Input:
        order_id = graphene.ID(required=True)
        user_id = graphene.ID(required=True)
        message = graphene.String(required=True)

    order_note = graphene.Field(OrderNoteType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, order_id, user_id, message):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            order = Order.objects.get(id=order_id)
            user = User.objects.get(id=user_id)
        except (Order.DoesNotExist, User.DoesNotExist):
            raise Exception("Order or User not found")

        order_note = OrderNote.objects.create(order=order, user=user, message=message)
        return AddOrderNoteMutation(order_note=order_note)


# Mutations
class OrderMutation(graphene.ObjectType):
    create_order = CreateOrderMutation.Field()
    update_order_status = UpdateOrderStatusMutation.Field()
    add_order_note = AddOrderNoteMutation.Field()


# Schema
class OrderSchema(graphene.Schema):
    query = OrderQuery
    mutation = OrderMutation
