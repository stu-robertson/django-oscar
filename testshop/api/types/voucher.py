from graphene_django import DjangoObjectType
import graphene
from oscar.apps.voucher.models import VoucherSet, Voucher, VoucherApplication
from oscar.apps.order.models import Order


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


class VoucherApplicationType(DjangoObjectType):
    class Meta:
        model = VoucherApplication
        fields = ("id", "voucher", "user", "order", "date_created")


# Queries
class VoucherQuery(graphene.ObjectType):
    voucher_sets = graphene.List(VoucherSetType)
    voucher_set = graphene.Field(VoucherSetType, id=graphene.ID(required=True))

    vouchers = graphene.List(VoucherType)
    voucher_by_code = graphene.Field(VoucherType, code=graphene.String(required=True))

    voucher_applications = graphene.List(VoucherApplicationType)
    voucher_applications_by_voucher = graphene.List(
        VoucherApplicationType, voucher_id=graphene.ID(required=True)
    )

    def resolve_voucher_sets(self, info):
        return VoucherSet.objects.all()

    def resolve_voucher_set(self, info, id):
        try:
            return VoucherSet.objects.get(id=id)
        except VoucherSet.DoesNotExist:
            return None

    def resolve_vouchers(self, info):
        return Voucher.objects.all()

    def resolve_voucher_by_code(self, info, code):
        try:
            return Voucher.objects.get(code=code.upper())
        except Voucher.DoesNotExist:
            return None

    def resolve_voucher_applications(self, info):
        return VoucherApplication.objects.all()

    def resolve_voucher_applications_by_voucher(self, info, voucher_id):
        try:
            return VoucherApplication.objects.filter(voucher_id=voucher_id)
        except VoucherApplication.DoesNotExist:
            return None


# Mutations
class CreateVoucherApplication(graphene.Mutation):
    class Arguments:
        voucher_id = graphene.ID(required=True)
        order_id = graphene.ID(required=True)
        user_id = graphene.ID()

    success = graphene.Boolean()

    def mutate(self, info, voucher_id, order_id, user_id=None):
        try:
            voucher = Voucher.objects.get(id=voucher_id)
            order = Order.objects.get(id=order_id)
            user = None if user_id is None else AUTH_USER_MODEL.objects.get(id=user_id)

            VoucherApplication.objects.create(voucher=voucher, order=order, user=user)
            return CreateVoucherApplication(success=True)
        except (Voucher.DoesNotExist, Order.DoesNotExist, AUTH_USER_MODEL.DoesNotExist):
            return CreateVoucherApplication(success=False)

class CreateVoucher(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        code = graphene.String(required=True)
        usage = graphene.String(required=True)  # SINGLE_USE, MULTI_USE, or ONCE_PER_CUSTOMER
        start_datetime = graphene.DateTime(required=True)
        end_datetime = graphene.DateTime(required=True)
        voucher_set_id = graphene.ID(required=False)

    voucher = graphene.Field(VoucherType)

    def mutate(self, info, name, code, usage, start_datetime, end_datetime, voucher_set_id=None):
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
            return CreateVoucher(voucher=voucher)
        except VoucherSet.DoesNotExist:
            raise Exception("Voucher Set not found")


class UpdateVoucher(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String()
        code = graphene.String()
        usage = graphene.String()
        start_datetime = graphene.DateTime()
        end_datetime = graphene.DateTime()

    voucher = graphene.Field(VoucherType)

    def mutate(self, info, id, name=None, code=None, usage=None, start_datetime=None, end_datetime=None):
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
            return UpdateVoucher(voucher=voucher)
        except Voucher.DoesNotExist:
            raise Exception("Voucher not found")


class DeleteVoucher(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        try:
            voucher = Voucher.objects.get(id=id)
            voucher.delete()
            return DeleteVoucher(success=True)
        except Voucher.DoesNotExist:
            return DeleteVoucher(success=False)


# Mutations
class VoucherMutation(graphene.ObjectType):
    create_voucher_application = CreateVoucherApplication.Field()
    create_voucher = CreateVoucher.Field()
    update_voucher = UpdateVoucher.Field()
    delete_voucher = DeleteVoucher.Field()


# Schema
class VoucherSchema(graphene.Schema):
    query = VoucherQuery
    mutation = VoucherMutation
