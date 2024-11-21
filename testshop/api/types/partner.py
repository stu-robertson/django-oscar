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


# Queries
class PartnerQuery(graphene.ObjectType):
    all_partners = graphene.List(PartnerType)
    partner_by_id = graphene.Field(PartnerType, id=graphene.ID(required=True))
    all_stock_records = graphene.List(StockRecordType)
    stock_record_by_id = graphene.Field(StockRecordType, id=graphene.ID(required=True))
    all_stock_alerts = graphene.List(StockAlertType)
    stock_alert_by_id = graphene.Field(StockAlertType, id=graphene.ID(required=True))

    def resolve_all_partners(self, info):
        return Partner.objects.all()

    def resolve_partner_by_id(self, info, id):
        try:
            return Partner.objects.get(id=id)
        except Partner.DoesNotExist:
            return None

    def resolve_all_stock_records(self, info):
        return StockRecord.objects.all()

    def resolve_stock_record_by_id(self, info, id):
        try:
            return StockRecord.objects.get(id=id)
        except StockRecord.DoesNotExist:
            return None

    def resolve_all_stock_alerts(self, info):
        return StockAlert.objects.all()

    def resolve_stock_alert_by_id(self, info, id):
        try:
            return StockAlert.objects.get(id=id)
        except StockAlert.DoesNotExist:
            return None

# Mutations for Partner
class CreatePartnerMutation(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        code = graphene.String(required=True)

    partner = graphene.Field(PartnerType)

    def mutate(self, info, name, code):
        partner = Partner.objects.create(name=name, code=code)
        return CreatePartnerMutation(partner=partner)


class UpdatePartnerMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String(required=False)
        code = graphene.String(required=False)

    partner = graphene.Field(PartnerType)

    def mutate(self, info, id, name=None, code=None):
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


class CreateStockRecordMutation(graphene.Mutation):
    class Arguments:
        partner_id = graphene.ID(required=True)
        product_id = graphene.ID(required=True)
        partner_sku = graphene.String(required=True)
        price_currency = graphene.String(required=True)
        price = graphene.Float(required=True)
        num_in_stock = graphene.Int(required=True)

    stock_record = graphene.Field(StockRecordType)

    def mutate(self, info, partner_id, product_id, partner_sku, price_currency, price, num_in_stock):
        try:
            from oscar.apps.catalogue.models import Product

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


class UpdateStockRecordMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        price = graphene.Float(required=False)
        num_in_stock = graphene.Int(required=False)

    stock_record = graphene.Field(StockRecordType)

    def mutate(self, info, id, price=None, num_in_stock=None):
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
