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


class OrderNoteType(DjangoObjectType):
    class Meta:
        model = OrderNote
        fields = ("id", "order", "user", "note_type", "message", "date_created")


class OrderStatusChangeType(DjangoObjectType):
    class Meta:
        model = OrderStatusChange
        fields = ("id", "order", "old_status", "new_status", "date_created")


class ShippingAddressType(DjangoObjectType):
    class Meta:
        model = ShippingAddress
        fields = ("id", "line1", "line2", "city", "postcode", "country")


class BillingAddressType(DjangoObjectType):
    class Meta:
        model = BillingAddress
        fields = ("id", "line1", "line2", "city", "postcode", "country")


class OrderDiscountType(DjangoObjectType):
    class Meta:
        model = OrderDiscount
        fields = ("id", "order", "offer_name", "voucher_code", "amount", "category")


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


class ShippingEventType(DjangoObjectType):
    class Meta:
        model = ShippingEvent
        fields = ("id", "order", "lines", "event_type", "date_created")


class PaymentEventType(DjangoObjectType):
    class Meta:
        model = PaymentEvent
        fields = ("id", "order", "amount", "reference", "event_type", "date_created")


class SurchargeType(DjangoObjectType):
    class Meta:
        model = Surcharge
        fields = ("id", "order", "name", "incl_tax", "excl_tax")


# Queries
class OrderQuery(graphene.ObjectType):
    orders = graphene.List(OrderType)
    order = graphene.Field(OrderType, id=graphene.ID(required=True))
    order_lines = graphene.List(LineType)
    line = graphene.Field(LineType, id=graphene.ID(required=True))
    shipping_addresses = graphene.List(ShippingAddressType)
    billing_addresses = graphene.List(BillingAddressType)
    order_notes = graphene.List(OrderNoteType)
    discounts = graphene.List(OrderDiscountType)

    def resolve_orders(self, info):
        return Order.objects.all()

    def resolve_order(self, info, id):
        try:
            return Order.objects.get(id=id)
        except Order.DoesNotExist:
            return None

    def resolve_order_lines(self, info):
        return Line.objects.all()

    def resolve_line(self, info, id):
        try:
            return Line.objects.get(id=id)
        except Line.DoesNotExist:
            return None

    def resolve_shipping_addresses(self, info):
        return ShippingAddress.objects.all()

    def resolve_billing_addresses(self, info):
        return BillingAddress.objects.all()

    def resolve_order_notes(self, info):
        return OrderNote.objects.all()

    def resolve_discounts(self, info):
        return OrderDiscount.objects.all()

# Mutations for Order
class CreateOrderMutation(graphene.Mutation):
    class Arguments:
        user_id = graphene.ID(required=True)
        billing_address_id = graphene.ID(required=True)
        shipping_address_id = graphene.ID(required=True)
        total_incl_tax = graphene.Float(required=True)
        total_excl_tax = graphene.Float(required=True)
        shipping_incl_tax = graphene.Float(required=True)
        shipping_excl_tax = graphene.Float(required=True)
        currency = graphene.String(required=True)
        status = graphene.String(required=False)

    order = graphene.Field(OrderType)

    def mutate(
        self,
        info,
        user_id,
        billing_address_id,
        shipping_address_id,
        total_incl_tax,
        total_excl_tax,
        shipping_incl_tax,
        shipping_excl_tax,
        currency,
        status=None,
    ):
        from django.contrib.auth import get_user_model
        from oscar.apps.order.models import Order

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


class UpdateOrderStatusMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        status = graphene.String(required=True)

    order = graphene.Field(OrderType)

    def mutate(self, info, id, status):
        try:
            order = Order.objects.get(id=id)
            order.status = status
            order.save()
            return UpdateOrderStatusMutation(order=order)
        except Order.DoesNotExist:
            raise Exception("Order not found")


class AddOrderNoteMutation(graphene.Mutation):
    class Arguments:
        order_id = graphene.ID(required=True)
        user_id = graphene.ID(required=True)
        message = graphene.String(required=True)

    order_note = graphene.Field(OrderNoteType)

    def mutate(self, info, order_id, user_id, message):
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
