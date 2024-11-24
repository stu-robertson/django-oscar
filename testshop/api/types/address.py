from graphene import relay
from graphene_django import DjangoObjectType
import graphene
from oscar.apps.address.models import UserAddress, Country


# GraphQL Type for Country
class CountryType(DjangoObjectType):
    class Meta:
        model = Country
        fields = (
            "iso_3166_1_a2",
            "iso_3166_1_a3",
            "iso_3166_1_numeric",
            "printable_name",
            "name",
            "display_order",
            "is_shipping_country",
        )
        interfaces = (relay.Node,)  # Add Relay interface for compatibility


# GraphQL Type for UserAddress
class UserAddressType(DjangoObjectType):
    class Meta:
        model = UserAddress
        fields = (
            "id",
            "user",
            "is_default_for_shipping",
            "is_default_for_billing",
            "num_orders_as_shipping_address",
            "num_orders_as_billing_address",
            "hash",
            "title",
            "first_name",
            "last_name",
            "line1",
            "line2",
            "line3",
            "line4",
            "state",
            "postcode",
            "country",
            "phone_number",
            "notes",
            "date_created",
        )
        interfaces = (relay.Node,)  # Add Relay interface for compatibility

    # Resolver for country to ensure proper serialization
    country = graphene.Field(CountryType)

    def resolve_country(self, info):
        return self.country


# GraphQL Query for Addresses
class AddressQuery(graphene.ObjectType):
    countries = relay.ConnectionField(relay.Connection.create_type('CountryConnection', node=CountryType))
    user_addresses = relay.ConnectionField(relay.Connection.create_type('UserAddressConnection', node=UserAddressType))
    user_address = relay.Node.Field(UserAddressType)

    def resolve_countries(self, info, **kwargs):
        return Country.objects.all()

    def resolve_user_addresses(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to view addresses.")
        return UserAddress.objects.filter(user=user)




# GraphQL Mutations for Addresses
class CreateUserAddressMutation(relay.ClientIDMutation):
    class Input:
        title = graphene.String()
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        line1 = graphene.String(required=True)
        line2 = graphene.String()
        line3 = graphene.String()
        line4 = graphene.String()
        state = graphene.String()
        postcode = graphene.String(required=True)
        country_id = graphene.ID(required=True)
        phone_number = graphene.String()
        notes = graphene.String()

    address = graphene.Field(UserAddressType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, **input):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to create an address.")

        try:
            country = Country.objects.get(id=input.pop("country_id"))
        except Country.DoesNotExist:
            raise Exception("Invalid country ID.")

        address = UserAddress(user=user, country=country, **input)
        address.save()
        return CreateUserAddressMutation(address=address)


class UpdateUserAddressMutation(relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)
        title = graphene.String()
        first_name = graphene.String()
        last_name = graphene.String()
        line1 = graphene.String()
        line2 = graphene.String()
        line3 = graphene.String()
        line4 = graphene.String()
        state = graphene.String()
        postcode = graphene.String()
        country_id = graphene.ID()
        phone_number = graphene.String()
        notes = graphene.String()

    address = graphene.Field(UserAddressType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, id, **input):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to update an address.")

        try:
            address = UserAddress.objects.get(id=id, user=user)
        except UserAddress.DoesNotExist:
            raise Exception("Address not found.")

        if "country_id" in input:
            try:
                input["country"] = Country.objects.get(id=input.pop("country_id"))
            except Country.DoesNotExist:
                raise Exception("Invalid country ID.")

        for field, value in input.items():
            setattr(address, field, value)

        address.save()
        return UpdateUserAddressMutation(address=address)


class DeleteUserAddressMutation(relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, id):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to delete an address.")

        try:
            address = UserAddress.objects.get(id=id, user=user)
        except UserAddress.DoesNotExist:
            raise Exception("Address not found.")

        address.delete()
        return DeleteUserAddressMutation(success=True)


# Mutations
class AddressMutation(graphene.ObjectType):
    create_user_address = CreateUserAddressMutation.Field()
    update_user_address = UpdateUserAddressMutation.Field()
    delete_user_address = DeleteUserAddressMutation.Field()


# Schema for Addresses
class AddressSchema(graphene.Schema):
    query = AddressQuery
    mutation = AddressMutation
