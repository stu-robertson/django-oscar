from graphene_django import DjangoObjectType
import graphene
from oscar.apps.customer.models import ProductAlert
from django.contrib.auth import get_user_model

# Fetch the custom user model
User = get_user_model()


# GraphQL Types
class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "date_joined",
        )


class ProductAlertType(DjangoObjectType):
    class Meta:
        model = ProductAlert
        fields = (
            "id",
            "product",
            "user",
            "email",
            "key",
            "status",
            "date_created",
            "date_confirmed",
            "date_cancelled",
            "date_closed",
        )


# Queries
class CustomerQuery(graphene.ObjectType):
    all_users = graphene.List(UserType)
    user_by_id = graphene.Field(UserType, id=graphene.ID(required=True))
    all_product_alerts = graphene.List(ProductAlertType)
    product_alerts_by_user = graphene.List(
        ProductAlertType, user_id=graphene.ID(required=True)
    )
    product_alert_by_id = graphene.Field(ProductAlertType, id=graphene.ID(required=True))

    def resolve_all_users(self, info):
        return User.objects.all()

    def resolve_user_by_id(self, info, id):
        try:
            return User.objects.get(id=id)
        except User.DoesNotExist:
            return None

    def resolve_all_product_alerts(self, info):
        return ProductAlert.objects.all()

    def resolve_product_alerts_by_user(self, info, user_id):
        return ProductAlert.objects.filter(user_id=user_id)

    def resolve_product_alert_by_id(self, info, id):
        try:
            return ProductAlert.objects.get(id=id)
        except ProductAlert.DoesNotExist:
            return None

# Mutations for Customer
class CreateUserMutation(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        password = graphene.String(required=True)

    user = graphene.Field(UserType)

    def mutate(self, info, email, first_name, last_name, password):
        user = User.objects.create_user(
            email=email, first_name=first_name, last_name=last_name, password=password
        )
        return CreateUserMutation(user=user)


class UpdateUserMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        first_name = graphene.String()
        last_name = graphene.String()

    user = graphene.Field(UserType)

    def mutate(self, info, id, first_name=None, last_name=None):
        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            raise Exception("User not found")

        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        user.save()
        return UpdateUserMutation(user=user)


class DeleteUserMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        try:
            user = User.objects.get(id=id)
            user.delete()
            return DeleteUserMutation(success=True)
        except User.DoesNotExist:
            raise Exception("User not found")


class CreateProductAlertMutation(graphene.Mutation):
    class Arguments:
        product_id = graphene.ID(required=True)
        email = graphene.String(required=True)

    product_alert = graphene.Field(ProductAlertType)

    def mutate(self, info, product_id, email):
        user = info.context.user if info.context.user.is_authenticated else None
        product_alert = ProductAlert.objects.create(product_id=product_id, email=email, user=user)
        return CreateProductAlertMutation(product_alert=product_alert)


class CancelProductAlertMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        try:
            product_alert = ProductAlert.objects.get(id=id)
            product_alert.cancel()
            return CancelProductAlertMutation(success=True)
        except ProductAlert.DoesNotExist:
            raise Exception("Product Alert not found")

# Mutations
class CustomerMutation(graphene.ObjectType):
    create_user = CreateUserMutation.Field()
    update_user = UpdateUserMutation.Field()
    delete_user = DeleteUserMutation.Field()
    create_product_alert = CreateProductAlertMutation.Field()
    cancel_product_alert = CancelProductAlertMutation.Field()


# Schema
class CustomerSchema(graphene.Schema):
    query = CustomerQuery
