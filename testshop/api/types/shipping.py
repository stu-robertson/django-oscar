from graphene_django import DjangoObjectType
import graphene
from oscar.apps.shipping.models import OrderAndItemCharges, WeightBased, WeightBand


# GraphQL Types
class OrderAndItemChargesType(DjangoObjectType):
    class Meta:
        model = OrderAndItemCharges
        fields = (
            "id",
            "code",
            "name",
            "description",
            "countries",
            "price_per_order",
            "price_per_item",
            "free_shipping_threshold",
        )


class WeightBasedType(DjangoObjectType):
    class Meta:
        model = WeightBased
        fields = (
            "id",
            "code",
            "name",
            "description",
            "countries",
            "weight_attribute",
            "default_weight",
            "num_bands",
            "top_band",
        )


class WeightBandType(DjangoObjectType):
    class Meta:
        model = WeightBand
        fields = (
            "id",
            "method",
            "upper_limit",
            "charge",
            "weight_from",
            "weight_to",
        )


# Queries
class ShippingQuery(graphene.ObjectType):
    order_and_item_charges = graphene.List(OrderAndItemChargesType)
    order_and_item_charge = graphene.Field(
        OrderAndItemChargesType, id=graphene.ID(required=True)
    )

    weight_based_methods = graphene.List(WeightBasedType)
    weight_based_method = graphene.Field(
        WeightBasedType, id=graphene.ID(required=True)
    )

    weight_bands_by_method = graphene.List(
        WeightBandType, method_id=graphene.ID(required=True)
    )

    def resolve_order_and_item_charges(self, info):
        return OrderAndItemCharges.objects.all()

    def resolve_order_and_item_charge(self, info, id):
        try:
            return OrderAndItemCharges.objects.get(id=id)
        except OrderAndItemCharges.DoesNotExist:
            return None

    def resolve_weight_based_methods(self, info):
        return WeightBased.objects.all()

    def resolve_weight_based_method(self, info, id):
        try:
            return WeightBased.objects.get(id=id)
        except WeightBased.DoesNotExist:
            return None

    def resolve_weight_bands_by_method(self, info, method_id):
        try:
            return WeightBand.objects.filter(method_id=method_id)
        except WeightBand.DoesNotExist:
            return None

# Mutations for Shipping
class CreateOrderAndItemChargeMutation(graphene.Mutation):
    class Arguments:
        code = graphene.String(required=True)
        name = graphene.String(required=True)
        description = graphene.String(required=False)
        price_per_order = graphene.Float(required=True)
        price_per_item = graphene.Float(required=True)
        free_shipping_threshold = graphene.Float(required=False)

    order_and_item_charge = graphene.Field(OrderAndItemChargesType)

    def mutate(
        self,
        info,
        code,
        name,
        description=None,
        price_per_order=None,
        price_per_item=None,
        free_shipping_threshold=None,
    ):
        order_and_item_charge = OrderAndItemCharges.objects.create(
            code=code,
            name=name,
            description=description,
            price_per_order=price_per_order,
            price_per_item=price_per_item,
            free_shipping_threshold=free_shipping_threshold,
        )
        return CreateOrderAndItemChargeMutation(order_and_item_charge=order_and_item_charge)


class CreateWeightBasedMethodMutation(graphene.Mutation):
    class Arguments:
        code = graphene.String(required=True)
        name = graphene.String(required=True)
        description = graphene.String(required=False)
        weight_attribute = graphene.String(required=False)
        default_weight = graphene.Float(required=True)

    weight_based_method = graphene.Field(WeightBasedType)

    def mutate(
        self,
        info,
        code,
        name,
        description=None,
        weight_attribute=None,
        default_weight=None,
    ):
        weight_based_method = WeightBased.objects.create(
            code=code,
            name=name,
            description=description,
            weight_attribute=weight_attribute,
            default_weight=default_weight,
        )
        return CreateWeightBasedMethodMutation(weight_based_method=weight_based_method)


class CreateWeightBandMutation(graphene.Mutation):
    class Arguments:
        method_id = graphene.ID(required=True)
        upper_limit = graphene.Float(required=True)
        charge = graphene.Float(required=True)

    weight_band = graphene.Field(WeightBandType)

    def mutate(self, info, method_id, upper_limit, charge):
        try:
            method = WeightBased.objects.get(id=method_id)
        except WeightBased.DoesNotExist:
            raise Exception("WeightBased method not found")

        weight_band = WeightBand.objects.create(
            method=method, upper_limit=upper_limit, charge=charge
        )
        return CreateWeightBandMutation(weight_band=weight_band)

# Mutations
class ShippingMutation(graphene.ObjectType):
    create_order_and_item_charge = CreateOrderAndItemChargeMutation.Field()
    create_weight_based_method = CreateWeightBasedMethodMutation.Field()
    create_weight_band = CreateWeightBandMutation.Field()


# Schema
class ShippingSchema(graphene.Schema):
    query = ShippingQuery
