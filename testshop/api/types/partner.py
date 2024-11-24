from graphene import relay
from graphene_django import DjangoObjectType
import graphene
from oscar.apps.partner.models import Partner, StockRecord, StockAlert


# GraphQL Types
class PartnerType(DjangoObjectType):
    class Meta:
        model = Partner
        fields = (
            "id",
            "name",
            "code",
            "users",
            "display_name",
            "primary_address",
        )
        interfaces = (relay.Node,)


class PartnerConnection(relay.Connection):
    class Meta:
        node = PartnerType


class StockRecordType(DjangoObjectType):
    class Meta:
        model = StockRecord
        fields = (
            "id",
            "product",
            "partner",
            "partner_sku",
            "price_currency",
            "price",
            "num_in_stock",
            "num_allocated",
            "low_stock_threshold",
            "net_stock_level",
            "is_below_threshold",
        )
        interfaces = (relay.Node,)


class StockRecordConnection(relay.Connection):
    class Meta:
        node = StockRecordType


class StockAlertType(DjangoObjectType):
    class Meta:
        model = StockAlert
        fields = (
            "id",
            "stockrecord",
            "threshold",
            "status",
            "date_created",
            "date_closed",
        )
        interfaces = (relay.Node,)


class StockAlertConnection(relay.Connection):
    class Meta:
        node = StockAlertType


# Queries
class PartnerQuery(graphene.ObjectType):
    partners = relay.ConnectionField(PartnerConnection)
    partner = relay.Node.Field(PartnerType)
    stock_records = relay.ConnectionField(StockRecordConnection)
    stock_record = relay.Node.Field(StockRecordType)
    stock_alerts = relay.ConnectionField(StockAlertConnection)
    stock_alert = relay.Node.Field(StockAlertType)

    def resolve_partners(self, info, **kwargs):
        return Partner.objects.all()

    def resolve_stock_records(self, info, **kwargs):
        return StockRecord.objects.all()

    def resolve_stock_alerts(self, info, **kwargs):
        return StockAlert.objects.all()


# Mutations for Partner
class CreatePartnerMutation(relay.ClientIDMutation):
    class Input:
        name = graphene.String(required=True)
        code = graphene.String(required=True)

    partner = graphene.Field(PartnerType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, name, code):
        partner = Partner.objects.create(name=name, code=code)
        return CreatePartnerMutation(partner=partner)


class UpdatePartnerMutation(relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)
        name = graphene.String()
        code = graphene.String()

    partner = graphene.Field(PartnerType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, id, name=None, code=None):
        try:
            partner = Partner.objects.get(id=id)
            if name:
                partner.name = name
            if code:
                partner.code = code
            partner.save()
            return UpdatePartnerMutation(partner=partner)
        except Partner.DoesNotExist:
            raise Exception("Partner not found")


class CreateStockRecordMutation(relay.ClientIDMutation):
    class Input:
        partner_id = graphene.ID(required=True)
        product_id = graphene.ID(required=True)
        partner_sku = graphene.String(required=True)
        price_currency = graphene.String(required=True)
        price = graphene.Float(required=True)
        num_in_stock = graphene.Int(required=True)

    stock_record = graphene.Field(StockRecordType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, partner_id, product_id, partner_sku,
                                price_currency, price, num_in_stock):
        from oscar.apps.catalogue.models import Product

        try:
            partner = Partner.objects.get(id=partner_id)
            product = Product.objects.get(id=product_id)
        except (Partner.DoesNotExist, Product.DoesNotExist):
            raise Exception("Invalid partner or product ID")

        stock_record = StockRecord.objects.create(
            partner=partner,
            product=product,
            partner_sku=partner_sku,
            price_currency=price_currency,
            price=price,
            num_in_stock=num_in_stock,
        )
        return CreateStockRecordMutation(stock_record=stock_record)


class UpdateStockRecordMutation(relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)
        price = graphene.Float()
        num_in_stock = graphene.Int()

    stock_record = graphene.Field(StockRecordType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, id, price=None, num_in_stock=None):
        try:
            stock_record = StockRecord.objects.get(id=id)
            if price is not None:
                stock_record.price = price
            if num_in_stock is not None:
                stock_record.num_in_stock = num_in_stock
            stock_record.save()
            return UpdateStockRecordMutation(stock_record=stock_record)
        except StockRecord.DoesNotExist:
            raise Exception("Stock record not found")


# Mutations
class PartnerMutation(graphene.ObjectType):
    create_partner = CreatePartnerMutation.Field()
    update_partner = UpdatePartnerMutation.Field()
    create_stock_record = CreateStockRecordMutation.Field()
    update_stock_record = UpdateStockRecordMutation.Field()


# Schema
class PartnerSchema(graphene.Schema):
    query = PartnerQuery
    mutation = PartnerMutation
