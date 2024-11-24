from graphene import relay
from graphene_django import DjangoObjectType
import graphene
from oscar.apps.offer.models import (
    ConditionalOffer,
    Benefit,
    Condition,
    Range,
    RangeProduct,
)


# GraphQL Types
class ConditionalOfferType(DjangoObjectType):
    class Meta:
        model = ConditionalOffer
        fields = (
            "id",
            "name",
            "description",
            "offer_type",
            "exclusive",
            "status",
            "condition",
            "benefit",
            "priority",
            "start_datetime",
            "end_datetime",
            "max_global_applications",
            "max_user_applications",
            "max_basket_applications",
            "max_discount",
            "total_discount",
            "num_applications",
            "num_orders",
            "redirect_url",
            "date_created",
        )
        interfaces = (relay.Node,)


class ConditionalOfferConnection(relay.Connection):
    class Meta:
        node = ConditionalOfferType


class BenefitType(DjangoObjectType):
    class Meta:
        model = Benefit
        fields = (
            "id",
            "range",
            "type",
            "value",
            "max_affected_items",
            "proxy_class",
        )
        interfaces = (relay.Node,)


class BenefitConnection(relay.Connection):
    class Meta:
        node = BenefitType


class ConditionType(DjangoObjectType):
    class Meta:
        model = Condition
        fields = (
            "id",
            "range",
            "type",
            "value",
            "proxy_class",
        )
        interfaces = (relay.Node,)


class ConditionConnection(relay.Connection):
    class Meta:
        node = ConditionType


class RangeType(DjangoObjectType):
    class Meta:
        model = Range
        fields = (
            "id",
            "name",
            "description",
            "is_public",
            "includes_products",
            "date_created",
        )
        interfaces = (relay.Node,)


class RangeConnection(relay.Connection):
    class Meta:
        node = RangeType


class RangeProductType(DjangoObjectType):
    class Meta:
        model = RangeProduct
        fields = (
            "id",
            "range",
            "product",
            "display_order",
        )
        interfaces = (relay.Node,)


class RangeProductConnection(relay.Connection):
    class Meta:
        node = RangeProductType


# Queries
class OfferQuery(graphene.ObjectType):
    offers = relay.ConnectionField(ConditionalOfferConnection)
    offer = relay.Node.Field(ConditionalOfferType)
    benefits = relay.ConnectionField(BenefitConnection)
    benefit = relay.Node.Field(BenefitType)
    conditions = relay.ConnectionField(ConditionConnection)
    condition = relay.Node.Field(ConditionType)
    ranges = relay.ConnectionField(RangeConnection)
    range = relay.Node.Field(RangeType)

    def resolve_offers(self, info, **kwargs):
        return ConditionalOffer.objects.all()

    def resolve_benefits(self, info, **kwargs):
        return Benefit.objects.all()

    def resolve_conditions(self, info, **kwargs):
        return Condition.objects.all()

    def resolve_ranges(self, info, **kwargs):
        return Range.objects.all()


# Mutations for Offer
class CreateConditionalOfferMutation(relay.ClientIDMutation):
    class Input:
        name = graphene.String(required=True)
        description = graphene.String()
        offer_type = graphene.String(required=True)
        condition_id = graphene.ID(required=True)
        benefit_id = graphene.ID(required=True)

    offer = graphene.Field(ConditionalOfferType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, name, offer_type, condition_id, benefit_id, description=None):
        try:
            condition = Condition.objects.get(id=condition_id)
            benefit = Benefit.objects.get(id=benefit_id)
        except (Condition.DoesNotExist, Benefit.DoesNotExist):
            raise Exception("Condition or Benefit not found")

        offer = ConditionalOffer.objects.create(
            name=name,
            description=description,
            offer_type=offer_type,
            condition=condition,
            benefit=benefit,
        )
        return CreateConditionalOfferMutation(offer=offer)


class UpdateConditionalOfferMutation(relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)
        name = graphene.String()
        description = graphene.String()
        offer_type = graphene.String()

    offer = graphene.Field(ConditionalOfferType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, id, name=None, description=None, offer_type=None):
        try:
            offer = ConditionalOffer.objects.get(id=id)
        except ConditionalOffer.DoesNotExist:
            raise Exception("Offer not found")

        if name:
            offer.name = name
        if description:
            offer.description = description
        if offer_type:
            offer.offer_type = offer_type

        offer.save()
        return UpdateConditionalOfferMutation(offer=offer)


class DeleteConditionalOfferMutation(relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, id):
        try:
            offer = ConditionalOffer.objects.get(id=id)
            offer.delete()
            return DeleteConditionalOfferMutation(success=True)
        except ConditionalOffer.DoesNotExist:
            raise Exception("Offer not found")


class CreateRangeMutation(relay.ClientIDMutation):
    class Input:
        name = graphene.String(required=True)
        description = graphene.String()
        is_public = graphene.Boolean()

    range = graphene.Field(RangeType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, name, description=None, is_public=True):
        range_obj = Range.objects.create(
            name=name, description=description, is_public=is_public
        )
        return CreateRangeMutation(range=range_obj)


class AddProductToRangeMutation(relay.ClientIDMutation):
    class Input:
        range_id = graphene.ID(required=True)
        product_id = graphene.ID(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, range_id, product_id):
        try:
            range_obj = Range.objects.get(id=range_id)
            range_obj.included_products.add(product_id)
            return AddProductToRangeMutation(success=True)
        except Range.DoesNotExist:
            raise Exception("Range not found")


# Mutations
class OfferMutation(graphene.ObjectType):
    create_conditional_offer = CreateConditionalOfferMutation.Field()
    update_conditional_offer = UpdateConditionalOfferMutation.Field()
    delete_conditional_offer = DeleteConditionalOfferMutation.Field()
    create_range = CreateRangeMutation.Field()
    add_product_to_range = AddProductToRangeMutation.Field()


# Schema
class OfferSchema(graphene.Schema):
    query = OfferQuery
    mutation = OfferMutation
