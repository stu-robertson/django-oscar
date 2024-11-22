from graphene_django import DjangoObjectType
import graphene
from oscar.apps.basket.models import Basket, Line, LineAttribute


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

    # Resolver for attributes to return related LineAttributes
    attributes = graphene.List(LineAttributeType)

    def resolve_attributes(self, info):
        return self.attributes.all()


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


# Queries for Basket
class BasketQuery(graphene.ObjectType):
    baskets = graphene.List(BasketType)
    basket = graphene.Field(BasketType, id=graphene.ID(required=True))
    lines = graphene.List(LineType)
    line = graphene.Field(LineType, id=graphene.ID(required=True))

    def resolve_baskets(self, info):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to view baskets.")
        return Basket.objects.filter(owner=user)

    def resolve_basket(self, info, id):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to view a basket.")
        try:
            return Basket.objects.get(id=id, owner=user)
        except Basket.DoesNotExist:
            raise Exception("Basket not found.")

    def resolve_lines(self, info):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to view basket lines.")
        return Line.objects.filter(basket__owner=user)

    def resolve_line(self, info, id):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to view a basket line.")
        try:
            return Line.objects.get(id=id, basket__owner=user)
        except Line.DoesNotExist:
            raise Exception("Line not found.")

# Mutations for Basket
class AddToBasketMutation(graphene.Mutation):
    class Arguments:
        product_id = graphene.ID(required=True)
        quantity = graphene.Int(required=True)

    basket = graphene.Field(BasketType)

    def mutate(self, info, product_id, quantity):
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


class RemoveFromBasketMutation(graphene.Mutation):
    class Arguments:
        line_id = graphene.ID(required=True)

    basket = graphene.Field(BasketType)

    def mutate(self, info, line_id):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to remove items from a basket.")

        try:
            line = Line.objects.get(id=line_id, basket__owner=user)
        except Line.DoesNotExist:
            raise Exception("Line not found.")

        basket = line.basket
        basket.lines.filter(id=line_id).delete()
        basket.save()
        return RemoveFromBasketMutation(basket=basket)


class UpdateBasketLineMutation(graphene.Mutation):
    class Arguments:
        line_id = graphene.ID(required=True)
        quantity = graphene.Int(required=True)

    basket = graphene.Field(BasketType)

    def mutate(self, info, line_id, quantity):
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
