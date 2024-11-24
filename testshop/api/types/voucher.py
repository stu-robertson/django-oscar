from graphene import relay
from graphene_django import DjangoObjectType
import graphene
from oscar.apps.voucher.models import VoucherSet, Voucher, VoucherApplication
from oscar.apps.order.models import Order
from django.contrib.auth import get_user_model

# Get the user model
AUTH_USER_MODEL = get_user_model()


# GraphQL Types
class VoucherSetType(DjangoObjectType):
    class Meta:
        model = VoucherSet
        fields = (
            "id",
            "name",
            "count",
            "code_length",
            "description",
            "start_datetime",
            "end_datetime",
            "num_basket_additions",
            "num_orders",
            "total_discount",
        )
        interfaces = (relay.Node,)


class VoucherSetConnection(relay.Connection):
    class Meta:
        node = VoucherSetType


class VoucherType(DjangoObjectType):
    class Meta:
        model = Voucher
        fields = (
            "id",
            "name",
            "code",
            "offers",
            "usage",
            "start_datetime",
            "end_datetime",
            "num_basket_additions",
            "num_orders",
            "total_discount",
            "voucher_set",
        )
        interfaces = (relay.Node,)


class VoucherConnection(relay.Connection):
    class Meta:
        node = VoucherType


class VoucherApplicationType(DjangoObjectType):
    class Meta:
        model = VoucherApplication
        fields = ("id", "voucher", "user", "order", "date_created")
        interfaces = (relay.Node,)


class VoucherApplicationConnection(relay.Connection):
    class Meta:
        node = VoucherApplicationType


# Queries
class VoucherQuery(graphene.ObjectType):
    voucher_sets = relay.ConnectionField(VoucherSetConnection)
    voucher_set = relay.Node.Field(VoucherSetType)

    vouchers = relay.ConnectionField(VoucherConnection)
    voucher_by_code = graphene.Field(VoucherType, code=graphene.String(required=True))

    voucher_applications = relay.ConnectionField(VoucherApplicationConnection)
    voucher_applications_by_voucher = relay.ConnectionField(
        VoucherApplicationConnection, voucher_id=graphene.ID(required=True)
    )

    def resolve_voucher_sets(self, info, **kwargs):
        return VoucherSet.objects.all()

    def resolve_vouchers(self, info, **kwargs):
        return Voucher.objects.all()

    def resolve_voucher_by_code(self, info, code):
        try:
            return Voucher.objects.get(code=code.upper())
        except Voucher.DoesNotExist:
            return None

    def resolve_voucher_applications(self, info, **kwargs):
        return VoucherApplication.objects.all()

    def resolve_voucher_applications_by_voucher(self, info, voucher_id, **kwargs):
        return VoucherApplication.objects.filter(voucher_id=voucher_id)


# Mutations
class CreateVoucherApplicationMutation(relay.ClientIDMutation):
    class Input:
        voucher_id = graphene.ID(required=True)
        order_id = graphene.ID(required=True)
        user_id = graphene.ID()

    success = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, voucher_id, order_id, user_id=None):
        try:
            voucher = Voucher.objects.get(id=voucher_id)
            order = Order.objects.get(id=order_id)
            user = None if user_id is None else AUTH_USER_MODEL.objects.get(id=user_id)

            VoucherApplication.objects.create(voucher=voucher, order=order, user=user)
            return CreateVoucherApplicationMutation(success=True)
        except (Voucher.DoesNotExist, Order.DoesNotExist, AUTH_USER_MODEL.DoesNotExist):
            return CreateVoucherApplicationMutation(success=False)


class CreateVoucherMutation(relay.ClientIDMutation):
    class Input:
        name = graphene.String(required=True)
        code = graphene.String(required=True)
        usage = graphene.String(required=True)  # SINGLE_USE, MULTI_USE, ONCE_PER_CUSTOMER
        start_datetime = graphene.DateTime(required=True)
        end_datetime = graphene.DateTime(required=True)
        voucher_set_id = graphene.ID()

    voucher = graphene.Field(VoucherType)

    @classmethod
    def mutate_and_get_payload(
        cls, root, info, name, code, usage, start_datetime, end_datetime, voucher_set_id=None
    ):
        try:
            voucher_set = None
            if voucher_set_id:
                voucher_set = VoucherSet.objects.get(id=voucher_set_id)
            voucher = Voucher.objects.create(
                name=name,
                code=code.upper(),
                usage=usage,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                voucher_set=voucher_set,
            )
            return CreateVoucherMutation(voucher=voucher)
        except VoucherSet.DoesNotExist:
            raise Exception("Voucher Set not found")


class UpdateVoucherMutation(relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)
        name = graphene.String()
        code = graphene.String()
        usage = graphene.String()
        start_datetime = graphene.DateTime()
        end_datetime = graphene.DateTime()

    voucher = graphene.Field(VoucherType)

    @classmethod
    def mutate_and_get_payload(
        cls, root, info, id, name=None, code=None, usage=None, start_datetime=None, end_datetime=None
    ):
        try:
            voucher = Voucher.objects.get(id=id)
            if name:
                voucher.name = name
            if code:
                voucher.code = code.upper()
            if usage:
                voucher.usage = usage
            if start_datetime:
                voucher.start_datetime = start_datetime
            if end_datetime:
                voucher.end_datetime = end_datetime
            voucher.save()
            return UpdateVoucherMutation(voucher=voucher)
        except Voucher.DoesNotExist:
            raise Exception("Voucher not found")


class DeleteVoucherMutation(relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, id):
        try:
            voucher = Voucher.objects.get(id=id)
            voucher.delete()
            return DeleteVoucherMutation(success=True)
        except Voucher.DoesNotExist:
            return DeleteVoucherMutation(success=False)


# Mutations
class VoucherMutation(graphene.ObjectType):
    create_voucher_application = CreateVoucherApplicationMutation.Field()
    create_voucher = CreateVoucherMutation.Field()
    update_voucher = UpdateVoucherMutation.Field()
    delete_voucher = DeleteVoucherMutation.Field()


# Schema
class VoucherSchema(graphene.Schema):
    query = VoucherQuery
    mutation = VoucherMutation
