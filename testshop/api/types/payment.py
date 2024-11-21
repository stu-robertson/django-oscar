from graphene_django import DjangoObjectType
import graphene
from oscar.apps.payment.models import Transaction, Source, SourceType, Bankcard


# GraphQL Types
class TransactionType(DjangoObjectType):
    class Meta:
        model = Transaction
        fields = (
            "id",
            "source",
            "txn_type",
            "amount",
            "reference",
            "status",
            "date_created",
        )


class SourceTypeType(DjangoObjectType):
    class Meta:
        model = SourceType
        fields = (
            "id",
            "name",
            "code",
        )


class SourceType(DjangoObjectType):
    class Meta:
        model = Source
        fields = (
            "id",
            "order",
            "source_type",
            "currency",
            "amount_allocated",
            "amount_debited",
            "amount_refunded",
            "reference",
            "label",
            "balance",
            "amount_available_for_refund",
        )


class BankcardType(DjangoObjectType):
    class Meta:
        model = Bankcard
        fields = (
            "id",
            "user",
            "card_type",
            "name",
            "number",
            "expiry_date",
            "partner_reference",
            "obfuscated_number",
        )


# Queries
class PaymentQuery(graphene.ObjectType):
    all_transactions = graphene.List(TransactionType)
    transaction_by_id = graphene.Field(TransactionType, id=graphene.ID(required=True))

    all_sources = graphene.List(SourceType)
    source_by_id = graphene.Field(SourceType, id=graphene.ID(required=True))

    all_source_types = graphene.List(SourceTypeType)
    source_type_by_id = graphene.Field(SourceTypeType, id=graphene.ID(required=True))

    all_bankcards = graphene.List(BankcardType)
    bankcard_by_id = graphene.Field(BankcardType, id=graphene.ID(required=True))

    def resolve_all_transactions(self, info):
        return Transaction.objects.all()

    def resolve_transaction_by_id(self, info, id):
        try:
            return Transaction.objects.get(id=id)
        except Transaction.DoesNotExist:
            return None

    def resolve_all_sources(self, info):
        return Source.objects.all()

    def resolve_source_by_id(self, info, id):
        try:
            return Source.objects.get(id=id)
        except Source.DoesNotExist:
            return None

    def resolve_all_source_types(self, info):
        return SourceType.objects.all()

    def resolve_source_type_by_id(self, info, id):
        try:
            return SourceType.objects.get(id=id)
        except SourceType.DoesNotExist:
            return None

    def resolve_all_bankcards(self, info):
        return Bankcard.objects.all()

    def resolve_bankcard_by_id(self, info, id):
        try:
            return Bankcard.objects.get(id=id)
        except Bankcard.DoesNotExist:
            return None

# Mutations for Payment
class CreateTransactionMutation(graphene.Mutation):
    class Arguments:
        source_id = graphene.ID(required=True)
        txn_type = graphene.String(required=True)
        amount = graphene.Float(required=True)
        reference = graphene.String(required=False)
        status = graphene.String(required=False)

    transaction = graphene.Field(TransactionType)

    def mutate(self, info, source_id, txn_type, amount, reference=None, status=None):
        try:
            source = Source.objects.get(id=source_id)
        except Source.DoesNotExist:
            raise Exception("Source not found")

        transaction = Transaction.objects.create(
            source=source,
            txn_type=txn_type,
            amount=amount,
            reference=reference,
            status=status,
        )
        return CreateTransactionMutation(transaction=transaction)


class CreateSourceMutation(graphene.Mutation):
    class Arguments:
        order_id = graphene.ID(required=True)
        source_type_id = graphene.ID(required=True)
        currency = graphene.String(required=True)
        amount_allocated = graphene.Float(required=True)
        reference = graphene.String(required=False)
        label = graphene.String(required=False)

    source = graphene.Field(SourceType)

    def mutate(
        self,
        info,
        order_id,
        source_type_id,
        currency,
        amount_allocated,
        reference=None,
        label=None,
    ):
        try:
            from oscar.apps.order.models import Order

            order = Order.objects.get(id=order_id)
            source_type = SourceType.objects.get(id=source_type_id)
        except Order.DoesNotExist:
            raise Exception("Order not found")
        except SourceType.DoesNotExist:
            raise Exception("SourceType not found")

        source = Source.objects.create(
            order=order,
            source_type=source_type,
            currency=currency,
            amount_allocated=amount_allocated,
            reference=reference,
            label=label,
        )
        return CreateSourceMutation(source=source)


class CreateBankcardMutation(graphene.Mutation):
    class Arguments:
        user_id = graphene.ID(required=True)
        card_type = graphene.String(required=True)
        name = graphene.String(required=False)
        number = graphene.String(required=True)
        expiry_date = graphene.String(required=True)
        partner_reference = graphene.String(required=False)

    bankcard = graphene.Field(BankcardType)

    def mutate(self, info, user_id, card_type, name, number, expiry_date, partner_reference=None):
        try:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise Exception("User not found")

        bankcard = Bankcard.objects.create(
            user=user,
            card_type=card_type,
            name=name,
            number=number,
            expiry_date=expiry_date,
            partner_reference=partner_reference,
        )
        return CreateBankcardMutation(bankcard=bankcard)

# Mutations
class PaymentMutation(graphene.ObjectType):
    create_transaction = CreateTransactionMutation.Field()
    create_source = CreateSourceMutation.Field()
    create_bankcard = CreateBankcardMutation.Field()


# Schema
class PaymentSchema(graphene.Schema):
    query = PaymentQuery
