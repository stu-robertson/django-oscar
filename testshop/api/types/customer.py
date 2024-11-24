from graphene import relay
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
        interfaces = (relay.Node,)


class UserConnection(relay.Connection):
    class Meta:
        node = UserType


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
        interfaces = (relay.Node,)


class ProductAlertConnection(relay.Connection):
    class Meta:
        node = ProductAlertType


# Queries
class CustomerQuery(graphene.ObjectType):
    users = relay.ConnectionField(UserConnection)
    user = relay.Node.Field(UserType)
    product_alerts = relay.ConnectionField(ProductAlertConnection)
    product_alerts_by_user = relay.ConnectionField(ProductAlertConnection, user_id=graphene.ID(required=True))
    product_alert = relay.Node.Field(ProductAlertType)

    def resolve_users(self, info, **kwargs):
        return User.objects.all()

    def resolve_product_alerts(self, info, **kwargs):
        return ProductAlert.objects.all()

    def resolve_product_alerts_by_user(self, info, user_id, **kwargs):
        return ProductAlert.objects.filter(user_id=user_id)


# Mutations for Customer
class CreateUserMutation(relay.ClientIDMutation):
    class Input:
        email = graphene.String(required=True)
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        password = graphene.String(required=True)

    user = graphene.Field(UserType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, email, first_name, last_name, password):
        user = User.objects.create_user(
            email=email, first_name=first_name, last_name=last_name, password=password
        )
        return CreateUserMutation(user=user)


class UpdateUserMutation(relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)
        first_name = graphene.String()
        last_name = graphene.String()

    user = graphene.Field(UserType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, id, first_name=None, last_name=None):
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


class DeleteUserMutation(relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, id):
        try:
            user = User.objects.get(id=id)
            user.delete()
            return DeleteUserMutation(success=True)
        except User.DoesNotExist:
            raise Exception("User not found")


class CreateProductAlertMutation(relay.ClientIDMutation):
    class Input:
        product_id = graphene.ID(required=True)
        email = graphene.String(required=True)

    product_alert = graphene.Field(ProductAlertType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, product_id, email):
        user = info.context.user if info.context.user.is_authenticated else None
        product_alert = ProductAlert.objects.create(product_id=product_id, email=email, user=user)
        return CreateProductAlertMutation(product_alert=product_alert)


class CancelProductAlertMutation(relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, id):
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
    mutation = CustomerMutation
