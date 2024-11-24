from graphene import relay
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
        interfaces = (relay.Node,)


class TransactionConnection(relay.Connection):
    class Meta:
        node = TransactionType


class SourceTypeType(DjangoObjectType):
    class Meta:
        model = SourceType
        fields = (
            "id",
            "name",
            "code",
        )
        interfaces = (relay.Node,)


class SourceTypeConnection(relay.Connection):
    class Meta:
        node = SourceTypeType


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
        interfaces = (relay.Node,)


class SourceConnection(relay.Connection):
    class Meta:
        node = SourceType


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
        interfaces = (relay.Node,)


class BankcardConnection(relay.Connection):
    class Meta:
        node = BankcardType


# Queries
class PaymentQuery(graphene.ObjectType):
    transactions = relay.ConnectionField(TransactionConnection)
    transaction = relay.Node.Field(TransactionType)

    sources = relay.ConnectionField(SourceConnection)
    source = relay.Node.Field(SourceType)

    source_types = relay.ConnectionField(SourceTypeConnection)
    source_type = relay.Node.Field(SourceTypeType)

    bankcards = relay.ConnectionField(BankcardConnection)
    bankcard = relay.Node.Field(BankcardType)

    def resolve_transactions(self, info, **kwargs):
        return Transaction.objects.all()

    def resolve_sources(self, info, **kwargs):
        return Source.objects.all()

    def resolve_source_types(self, info, **kwargs):
        return SourceType.objects.all()

    def resolve_bankcards(self, info, **kwargs):
        return Bankcard.objects.all()


# Mutations for Payment
class CreateTransactionMutation(relay.ClientIDMutation):
    class Input:
        source_id = graphene.ID(required=True)
        txn_type = graphene.String(required=True)
        amount = graphene.Float(required=True)
        reference = graphene.String(required=False)
        status = graphene.String(required=False)

    transaction = graphene.Field(TransactionType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, source_id, txn_type, amount, reference=None, status=None):
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


class CreateSourceMutation(relay.ClientIDMutation):
    class Input:
        order_id = graphene.ID(required=True)
        source_type_id = graphene.ID(required=True)
        currency = graphene.String(required=True)
        amount_allocated = graphene.Float(required=True)
        reference = graphene.String(required=False)
        label = graphene.String(required=False)

    source = graphene.Field(SourceType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, order_id, source_type_id, currency, amount_allocated, reference=None, label=None):
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


class CreateBankcardMutation(relay.ClientIDMutation):
    class Input:
        user_id = graphene.ID(required=True)
        card_type = graphene.String(required=True)
        name = graphene.String(required=False)
        number = graphene.String(required=True)
        expiry_date = graphene.String(required=True)
        partner_reference = graphene.String(required=False)

    bankcard = graphene.Field(BankcardType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, user_id, card_type, name, number, expiry_date, partner_reference=None):
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
    mutation = PaymentMutation
