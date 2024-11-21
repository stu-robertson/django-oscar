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


class RangeType(DjangoObjectType):
    class Meta:
        model = Range
        fields = (
            "id",
            "name",
            "description",
            "is_public",
            "includes_all_products",
            "date_created",
        )


class RangeProductType(DjangoObjectType):
    class Meta:
        model = RangeProduct
        fields = (
            "id",
            "range",
            "product",
            "display_order",
        )


# Queries
class OfferQuery(graphene.ObjectType):
    all_offers = graphene.List(ConditionalOfferType)
    offer_by_id = graphene.Field(ConditionalOfferType, id=graphene.ID(required=True))
    all_benefits = graphene.List(BenefitType)
    benefit_by_id = graphene.Field(BenefitType, id=graphene.ID(required=True))
    all_conditions = graphene.List(ConditionType)
    condition_by_id = graphene.Field(ConditionType, id=graphene.ID(required=True))
    all_ranges = graphene.List(RangeType)
    range_by_id = graphene.Field(RangeType, id=graphene.ID(required=True))

    def resolve_all_offers(self, info):
        return ConditionalOffer.objects.all()

    def resolve_offer_by_id(self, info, id):
        try:
            return ConditionalOffer.objects.get(id=id)
        except ConditionalOffer.DoesNotExist:
            return None

    def resolve_all_benefits(self, info):
        return Benefit.objects.all()

    def resolve_benefit_by_id(self, info, id):
        try:
            return Benefit.objects.get(id=id)
        except Benefit.DoesNotExist:
            return None

    def resolve_all_conditions(self, info):
        return Condition.objects.all()

    def resolve_condition_by_id(self, info, id):
        try:
            return Condition.objects.get(id=id)
        except Condition.DoesNotExist:
            return None

    def resolve_all_ranges(self, info):
        return Range.objects.all()

    def resolve_range_by_id(self, info, id):
        try:
            return Range.objects.get(id=id)
        except Range.DoesNotExist:
            return None

# Mutations for Offer
class CreateConditionalOfferMutation(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String(required=False)
        offer_type = graphene.String(required=True)
        condition_id = graphene.ID(required=True)
        benefit_id = graphene.ID(required=True)

    offer = graphene.Field(ConditionalOfferType)

    def mutate(self, info, name, offer_type, condition_id, benefit_id, description=None):
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


class UpdateConditionalOfferMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String(required=False)
        description = graphene.String(required=False)
        offer_type = graphene.String(required=False)

    offer = graphene.Field(ConditionalOfferType)

    def mutate(self, info, id, name=None, description=None, offer_type=None):
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


class DeleteConditionalOfferMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        try:
            offer = ConditionalOffer.objects.get(id=id)
            offer.delete()
            return DeleteConditionalOfferMutation(success=True)
        except ConditionalOffer.DoesNotExist:
            raise Exception("Offer not found")


class CreateRangeMutation(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String(required=False)
        is_public = graphene.Boolean(required=False)

    range = graphene.Field(RangeType)

    def mutate(self, info, name, description=None, is_public=True):
        range_obj = Range.objects.create(
            name=name, description=description, is_public=is_public
        )
        return CreateRangeMutation(range=range_obj)


class AddProductToRangeMutation(graphene.Mutation):
    class Arguments:
        range_id = graphene.ID(required=True)
        product_id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, range_id, product_id):
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
