from graphene import relay
from graphene_django import DjangoObjectType
import graphene
from oscar.apps.analytics.models import ProductRecord, UserRecord, UserProductView, UserSearch


# GraphQL Type for ProductRecord
class ProductRecordType(DjangoObjectType):
    class Meta:
        model = ProductRecord
        fields = (
            "product",
            "num_views",
            "num_basket_additions",
            "num_purchases",
            "score",
        )
        interfaces = (relay.Node,)  # Add Relay interface


class ProductRecordConnection(relay.Connection):
    class Meta:
        node = ProductRecordType


# GraphQL Type for UserRecord
class UserRecordType(DjangoObjectType):
    class Meta:
        model = UserRecord
        fields = (
            "user",
            "num_product_views",
            "num_basket_additions",
            "num_orders",
            "num_order_lines",
            "num_order_items",
            "total_spent",
            "date_last_order",
        )
        interfaces = (relay.Node,)  # Add Relay interface


class UserRecordConnection(relay.Connection):
    class Meta:
        node = UserRecordType


# GraphQL Type for UserProductView
class UserProductViewType(DjangoObjectType):
    class Meta:
        model = UserProductView
        fields = (
            "user",
            "product",
            "date_created",
        )
        interfaces = (relay.Node,)  # Add Relay interface


class UserProductViewConnection(relay.Connection):
    class Meta:
        node = UserProductViewType


# GraphQL Type for UserSearch
class UserSearchType(DjangoObjectType):
    class Meta:
        model = UserSearch
        fields = (
            "user",
            "query",
            "date_created",
        )
        interfaces = (relay.Node,)  # Add Relay interface


class UserSearchConnection(relay.Connection):
    class Meta:
        node = UserSearchType


# Queries for Analytics
class AnalyticsQuery(graphene.ObjectType):
    product_records = relay.ConnectionField(ProductRecordConnection)
    user_records = relay.ConnectionField(UserRecordConnection)
    user_product_views = relay.ConnectionField(UserProductViewConnection)
    user_searches = relay.ConnectionField(UserSearchConnection)

    product_record = relay.Node.Field(ProductRecordType)
    user_record = relay.Node.Field(UserRecordType)

    def resolve_product_records(self, info, **kwargs):
        return ProductRecord.objects.all()

    def resolve_user_records(self, info, **kwargs):
        return UserRecord.objects.all()

    def resolve_user_product_views(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to view user product views.")
        return UserProductView.objects.filter(user=user)

    def resolve_user_searches(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to view user searches.")
        return UserSearch.objects.filter(user=user)


# Mutations for Analytics
class CreateUserProductViewMutation(relay.ClientIDMutation):
    class Input:
        product_id = graphene.ID(required=True)

    user_product_view = graphene.Field(UserProductViewType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, product_id):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to record a product view.")

        try:
            product_record = ProductRecord.objects.get(product_id=product_id)
        except ProductRecord.DoesNotExist:
            raise Exception("Product not found.")

        user_product_view = UserProductView.objects.create(user=user, product=product_record.product)
        return CreateUserProductViewMutation(user_product_view=user_product_view)


class CreateUserSearchMutation(relay.ClientIDMutation):
    class Input:
        query = graphene.String(required=True)

    user_search = graphene.Field(UserSearchType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, query):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to record a search.")

        user_search = UserSearch.objects.create(user=user, query=query)
        return CreateUserSearchMutation(user_search=user_search)


# Mutations
class AnalyticsMutation(graphene.ObjectType):
    create_user_product_view = CreateUserProductViewMutation.Field()
    create_user_search = CreateUserSearchMutation.Field()


# Schema for Analytics
class AnalyticsSchema(graphene.Schema):
    query = AnalyticsQuery
    mutation = AnalyticsMutation
