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


# GraphQL Type for UserProductView
class UserProductViewType(DjangoObjectType):
    class Meta:
        model = UserProductView
        fields = (
            "user",
            "product",
            "date_created",
        )


# GraphQL Type for UserSearch
class UserSearchType(DjangoObjectType):
    class Meta:
        model = UserSearch
        fields = (
            "user",
            "query",
            "date_created",
        )


# Queries for Analytics
class AnalyticsQuery(graphene.ObjectType):
    all_product_records = graphene.List(ProductRecordType)
    all_user_records = graphene.List(UserRecordType)
    all_user_product_views = graphene.List(UserProductViewType)
    all_user_searches = graphene.List(UserSearchType)

    product_record = graphene.Field(ProductRecordType, product_id=graphene.ID(required=True))
    user_record = graphene.Field(UserRecordType, user_id=graphene.ID(required=True))

    def resolve_all_product_records(self, info):
        return ProductRecord.objects.all()

    def resolve_all_user_records(self, info):
        return UserRecord.objects.all()

    def resolve_all_user_product_views(self, info):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to view user product views.")
        return UserProductView.objects.filter(user=user)

    def resolve_all_user_searches(self, info):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to view user searches.")
        return UserSearch.objects.filter(user=user)

    def resolve_product_record(self, info, product_id):
        try:
            return ProductRecord.objects.get(product_id=product_id)
        except ProductRecord.DoesNotExist:
            raise Exception("Product record not found.")

    def resolve_user_record(self, info, user_id):
        try:
            return UserRecord.objects.get(user_id=user_id)
        except UserRecord.DoesNotExist:
            raise Exception("User record not found.")

# Mutations for Analytics
class CreateUserProductViewMutation(graphene.Mutation):
    class Arguments:
        product_id = graphene.ID(required=True)

    user_product_view = graphene.Field(UserProductViewType)

    def mutate(self, info, product_id):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to record a product view.")

        try:
            product_record = ProductRecord.objects.get(product_id=product_id)
        except ProductRecord.DoesNotExist:
            raise Exception("Product not found.")

        user_product_view = UserProductView.objects.create(user=user, product=product_record.product)
        return CreateUserProductViewMutation(user_product_view=user_product_view)


class CreateUserSearchMutation(graphene.Mutation):
    class Arguments:
        query = graphene.String(required=True)

    user_search = graphene.Field(UserSearchType)

    def mutate(self, info, query):
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
