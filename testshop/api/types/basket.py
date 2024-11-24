from graphene import relay
from graphene_django import DjangoObjectType
import graphene
from oscar.apps.basket.models import Basket, Line, LineAttribute
from oscar.apps.catalogue.models import Product  # Required for mutations


# GraphQL Type for LineAttribute
class LineAttributeType(DjangoObjectType):
    class Meta:
        model = LineAttribute
        fields = (
            "id",
            "line",
            "option",
            "value",
        )
        interfaces = (relay.Node,)


class LineAttributeConnection(relay.Connection):
    class Meta:
        node = LineAttributeType


# GraphQL Type for Line
class LineType(DjangoObjectType):
    class Meta:
        model = Line
        fields = (
            "id",
            "basket",
            "line_reference",
            "product",
            "stockrecord",
            "quantity",
            "price_currency",
            "price_excl_tax",
            "price_incl_tax",
            "tax_code",
            "date_created",
            "date_updated",
            "attributes",
        )
        interfaces = (relay.Node,)

    # Resolver for attributes to return related LineAttributes
    attributes = relay.ConnectionField(LineAttributeConnection)

    def resolve_attributes(self, info, **kwargs):
        return self.attributes.all()


class LineConnection(relay.Connection):
    class Meta:
        node = LineType


# GraphQL Type for Basket
class BasketType(DjangoObjectType):
    class Meta:
        model = Basket
        fields = (
            "id",
            "owner",
            "status",
            "vouchers",
            "date_created",
            "date_merged",
            "date_submitted",
            "num_items",
            "num_lines",
            "total_incl_tax",
            "total_excl_tax",
            "total_discount",
            "is_empty",
            "is_shipping_required",
        )
        interfaces = (relay.Node,)

    # Additional computed fields
    num_items = graphene.Int()
    num_lines = graphene.Int()
    total_incl_tax = graphene.Float()
    total_excl_tax = graphene.Float()
    total_discount = graphene.Float()

    def resolve_num_items(self, info):
        return self.num_items

    def resolve_num_lines(self, info):
        return self.num_lines

    def resolve_total_incl_tax(self, info):
        return self.total_incl_tax

    def resolve_total_excl_tax(self, info):
        return self.total_excl_tax

    def resolve_total_discount(self, info):
        return self.total_discount


class BasketConnection(relay.Connection):
    class Meta:
        node = BasketType


# Queries for Basket
class BasketQuery(graphene.ObjectType):
    baskets = relay.ConnectionField(BasketConnection)
    basket = relay.Node.Field(BasketType)
    lines = relay.ConnectionField(LineConnection)
    line = relay.Node.Field(LineType)

    def resolve_baskets(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to view baskets.")
        return Basket.objects.filter(owner=user)

    def resolve_lines(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to view basket lines.")
        return Line.objects.filter(basket__owner=user)


# Mutations for Basket
class AddToBasketMutation(relay.ClientIDMutation):
    class Input:
        product_id = graphene.ID(required=True)
        quantity = graphene.Int(required=True)

    basket = graphene.Field(BasketType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, product_id, quantity):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to add items to a basket.")

        basket, _ = Basket.objects.get_or_create(owner=user, status=Basket.OPEN)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise Exception("Product not found.")

        basket.add_product(product, quantity=quantity)
        return AddToBasketMutation(basket=basket)


class RemoveFromBasketMutation(relay.ClientIDMutation):
    class Input:
        line_id = graphene.ID(required=True)

    basket = graphene.Field(BasketType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, line_id):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to remove items from a basket.")

        try:
            line = Line.objects.get(id=line_id, basket__owner=user)
        except Line.DoesNotExist:
            raise Exception("Line not found.")

        basket = line.basket
        line.delete()
        basket.save()
        return RemoveFromBasketMutation(basket=basket)


class UpdateBasketLineMutation(relay.ClientIDMutation):
    class Input:
        line_id = graphene.ID(required=True)
        quantity = graphene.Int(required=True)

    basket = graphene.Field(BasketType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, line_id, quantity):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to update basket lines.")

        try:
            line = Line.objects.get(id=line_id, basket__owner=user)
        except Line.DoesNotExist:
            raise Exception("Line not found.")

        if quantity <= 0:
            raise Exception("Quantity must be greater than zero.")

        line.quantity = quantity
        line.save()
        return UpdateBasketLineMutation(basket=line.basket)


# Mutations
class BasketMutation(graphene.ObjectType):
    add_to_basket = AddToBasketMutation.Field()
    remove_from_basket = RemoveFromBasketMutation.Field()
    update_basket_line = UpdateBasketLineMutation.Field()


# Schema for Basket
class BasketSchema(graphene.Schema):
    query = BasketQuery
    mutation = BasketMutation
