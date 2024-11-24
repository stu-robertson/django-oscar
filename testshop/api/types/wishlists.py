from graphene import relay
from graphene_django import DjangoObjectType
import graphene
import logging
from graphene.relay import Node
from graphql_relay import from_global_id
from oscar.apps.wishlists.models import WishList, Line, WishListSharedEmail
from oscar.apps.catalogue.models import Product
from oscar.core.compat import AUTH_USER_MODEL
from graphene import Enum


class VisibilityEnum(Enum):
    PRIVATE = "Private"
    SHARED = "Shared"
    PUBLIC = "Public"

# Define LineType and LineConnection before using them
class LineType(DjangoObjectType):
    class Meta:
        model = Line
        fields = (
            "id",
            "wishlist",
            "product",
            "quantity",
            "title",
        )
        interfaces = (relay.Node,)

    def resolve_product(self, info):
        return self.product

class LineConnection(relay.Connection):
    class Meta:
        node = LineType

# Now define WishListType
class WishListType(DjangoObjectType):
    lines = graphene.List(LineType)

    class Meta:
        model = WishList
        fields = (
            "id",
            "owner",
            "name",
            "key",
            "visibility",
            "date_created",
            "shared_emails",
            "is_shareable",
            "lines",
        )
        interfaces = (relay.Node,)

    def resolve_lines(self, info):
        return self.lines.all()


class WishListConnection(relay.Connection):
    class Meta:
        node = WishListType

class WishListSharedEmailType(DjangoObjectType):
    class Meta:
        model = WishListSharedEmail
        fields = ("id", "wishlist", "email")
        interfaces = (relay.Node,)

class WishListSharedEmailConnection(relay.Connection):
    class Meta:
        node = WishListSharedEmailType

# Queries
class WishListQuery(graphene.ObjectType):
    wishlist = graphene.Field(WishListType, id=graphene.ID(required=True))
    wishlists = relay.ConnectionField(WishListConnection)
    wishlist_by_key = graphene.Field(WishListType, key=graphene.String(required=True))
    wishlist_lines = relay.ConnectionField(LineConnection, wishlist_id=graphene.ID(required=True))

    def resolve_wishlist(self, info, id):
        user = info.context.user
        try:
            # Decode the global ID
            _, decoded_id = from_global_id(id)
            wishlist = WishList.objects.get(id=decoded_id)
            if wishlist.is_allowed_to_see(user):
                return wishlist
            else:
                raise Exception("Not authorized to view this wishlist.")
        except WishList.DoesNotExist:
            return None

    def resolve_wishlists(self, info, **kwargs):
        user = info.context.user
        if user.is_authenticated:
            return WishList.objects.filter(owner=user)
        return []

    def resolve_wishlist_by_key(self, info, key):
        user = info.context.user
        try:
            wishlist = WishList.objects.get(key=key)
            if wishlist.is_allowed_to_see(user):
                return wishlist
        except WishList.DoesNotExist:
            return None

    def resolve_wishlist_lines(self, info, wishlist_id, **kwargs):
        try:
            wishlist = WishList.objects.get(id=wishlist_id)
            if wishlist.is_allowed_to_see(info.context.user):
                return wishlist.lines.all()
        except WishList.DoesNotExist:
            return []


# Mutations
class CreateWishListMutation(relay.ClientIDMutation):
    class Input:
        name = graphene.String(required=True)
        visibility = VisibilityEnum(default_value=VisibilityEnum.PRIVATE)

    wishlist = graphene.Field(WishListType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, name, visibility):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to create a wishlist.")
        wishlist = WishList.objects.create(owner=user, name=name, visibility=visibility.value)
        return CreateWishListMutation(wishlist=wishlist)

logger = logging.getLogger(__name__)

class AddToWishListMutation(relay.ClientIDMutation):
    class Input:
        wishlist_id = graphene.ID(required=True)
        product_id = graphene.ID(required=True)

    wishlist = graphene.Field(WishListType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, wishlist_id, product_id):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to add to wishlist.")

        # Decode global IDs
        _, decoded_wishlist_id = from_global_id(wishlist_id)
        _, decoded_product_id = from_global_id(product_id)

        try:
            wishlist = WishList.objects.get(id=decoded_wishlist_id)
            product = Product.objects.get(id=decoded_product_id)

            if not wishlist.is_allowed_to_edit(user):
                raise Exception("Not authorized to edit this wishlist.")

            wishlist.add(product)  # Add product to wishlist
            wishlist.refresh_from_db()  # Refresh to include new lines
            return AddToWishListMutation(wishlist=wishlist)

        except WishList.DoesNotExist:
            raise Exception("Invalid wishlist ID.")
        except Product.DoesNotExist:
            raise Exception("Invalid product ID.")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")

class RemoveFromWishListMutation(relay.ClientIDMutation):
    class Input:
        wishlist_id = graphene.ID(required=True)
        product_id = graphene.ID(required=True)

    wishlist = graphene.Field(WishListType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, wishlist_id, product_id):
        user = info.context.user
        try:
            wishlist = WishList.objects.get(id=wishlist_id)
            product = Product.objects.get(id=product_id)

            if wishlist.is_allowed_to_edit(user):
                line = wishlist.lines.filter(product=product).first()
                if line:
                    line.delete()
                return RemoveFromWishListMutation(wishlist=wishlist)
        except (WishList.DoesNotExist, Product.DoesNotExist):
            raise Exception("Invalid wishlist or product ID.")
        raise Exception("Not authorized to edit this wishlist.")

class ShareWishListMutation(relay.ClientIDMutation):
    class Input:
        wishlist_id = graphene.ID(required=True)
        email = graphene.String(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, wishlist_id, email):
        user = info.context.user
        try:
            wishlist = WishList.objects.get(id=wishlist_id)
            if wishlist.is_allowed_to_edit(user):
                WishListSharedEmail.objects.create(wishlist=wishlist, email=email)
                return ShareWishListMutation(success=True)
        except WishList.DoesNotExist:
            raise Exception("Invalid wishlist ID.")
        raise Exception("Not authorized to share this wishlist.")

class DeleteWishListMutation(relay.ClientIDMutation):
    class Input:
        wishlist_id = graphene.ID(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, wishlist_id):
        user = info.context.user
        try:
            wishlist = WishList.objects.get(id=wishlist_id)
            if wishlist.is_allowed_to_edit(user):
                wishlist.delete()
                return DeleteWishListMutation(success=True)
        except WishList.DoesNotExist:
            raise Exception("Invalid wishlist ID.")
        raise Exception("Not authorized to delete this wishlist.")

class UpdateWishListMutation(relay.ClientIDMutation):
    class Input:
        wishlist_id = graphene.ID(required=True)
        name = graphene.String()
        visibility = graphene.String()

    wishlist = graphene.Field(WishListType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, wishlist_id, name=None, visibility=None):
        user = info.context.user
        try:
            wishlist = WishList.objects.get(id=wishlist_id)
            if wishlist.is_allowed_to_edit(user):
                if name:
                    wishlist.name = name
                if visibility:
                    wishlist.visibility = visibility
                wishlist.save()
                return UpdateWishListMutation(wishlist=wishlist)
        except WishList.DoesNotExist:
            raise Exception("Invalid wishlist ID.")
        raise Exception("Not authorized to update this wishlist.")

# Mutations
class WishListMutation(graphene.ObjectType):
    create_wishlist = CreateWishListMutation.Field()
    add_to_wishlist = AddToWishListMutation.Field()
    remove_from_wishlist = RemoveFromWishListMutation.Field()
    delete_wishlist = DeleteWishListMutation.Field()
    update_wishlist = UpdateWishListMutation.Field()
    share_wishlist = ShareWishListMutation.Field()

# Schema
class WishListSchema(graphene.Schema):
    query = WishListQuery
    mutation = WishListMutation
