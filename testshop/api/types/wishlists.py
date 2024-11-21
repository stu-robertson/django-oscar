from graphene_django import DjangoObjectType
import graphene
from oscar.apps.wishlists.models import WishList, Line, WishListSharedEmail
from oscar.apps.catalogue.models import Product
from oscar.core.compat import AUTH_USER_MODEL


# GraphQL Types
class WishListType(DjangoObjectType):
    class Meta:
        model = WishList
        fields = (
            "id",
            "owner",
            "name",
            "key",
            "visibility",
            "date_created",
            "lines",
            "shared_emails",
            "is_shareable",
        )


class LineType(DjangoObjectType):
    class Meta:
        model = Line
        fields = ("id", "wishlist", "product", "quantity", "title")


class WishListSharedEmailType(DjangoObjectType):
    class Meta:
        model = WishListSharedEmail
        fields = ("id", "wishlist", "email")


# Queries
class WishListQuery(graphene.ObjectType):
    all_wishlists = graphene.List(WishListType)
    wishlist_by_key = graphene.Field(WishListType, key=graphene.String(required=True))
    wishlist_lines = graphene.List(LineType, wishlist_id=graphene.ID(required=True))

    def resolve_all_wishlists(self, info):
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

    def resolve_wishlist_lines(self, info, wishlist_id):
        try:
            wishlist = WishList.objects.get(id=wishlist_id)
            if wishlist.is_allowed_to_see(info.context.user):
                return wishlist.lines.all()
        except WishList.DoesNotExist:
            return []
        return []


# Mutations
class CreateWishList(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        visibility = graphene.String(default_value=WishList.PRIVATE)

    wishlist = graphene.Field(WishListType)

    def mutate(self, info, name, visibility):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to create a wishlist.")
        wishlist = WishList.objects.create(owner=user, name=name, visibility=visibility)
        return CreateWishList(wishlist=wishlist)


class AddToWishList(graphene.Mutation):
    class Arguments:
        wishlist_id = graphene.ID(required=True)
        product_id = graphene.ID(required=True)

    wishlist = graphene.Field(WishListType)

    def mutate(self, info, wishlist_id, product_id):
        user = info.context.user
        try:
            wishlist = WishList.objects.get(id=wishlist_id)
            product = Product.objects.get(id=product_id)

            if wishlist.is_allowed_to_edit(user):
                wishlist.add(product)
                return AddToWishList(wishlist=wishlist)
        except (WishList.DoesNotExist, Product.DoesNotExist):
            raise Exception("Invalid wishlist or product ID.")
        raise Exception("Not authorized to edit this wishlist.")


class ShareWishList(graphene.Mutation):
    class Arguments:
        wishlist_id = graphene.ID(required=True)
        email = graphene.String(required=True)

    success = graphene.Boolean()

    def mutate(self, info, wishlist_id, email):
        user = info.context.user
        try:
            wishlist = WishList.objects.get(id=wishlist_id)
            if wishlist.is_allowed_to_edit(user):
                WishListSharedEmail.objects.create(wishlist=wishlist, email=email)
                return ShareWishList(success=True)
        except WishList.DoesNotExist:
            raise Exception("Invalid wishlist ID.")
        raise Exception("Not authorized to share this wishlist.")

class RemoveFromWishList(graphene.Mutation):
    class Arguments:
        wishlist_id = graphene.ID(required=True)
        product_id = graphene.ID(required=True)

    wishlist = graphene.Field(WishListType)

    def mutate(self, info, wishlist_id, product_id):
        user = info.context.user
        try:
            wishlist = WishList.objects.get(id=wishlist_id)
            product = Product.objects.get(id=product_id)

            if wishlist.is_allowed_to_edit(user):
                line = wishlist.lines.filter(product=product).first()
                if line:
                    line.delete()
                return RemoveFromWishList(wishlist=wishlist)
        except (WishList.DoesNotExist, Product.DoesNotExist):
            raise Exception("Invalid wishlist or product ID.")
        raise Exception("Not authorized to edit this wishlist.")


class DeleteWishList(graphene.Mutation):
    class Arguments:
        wishlist_id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, wishlist_id):
        user = info.context.user
        try:
            wishlist = WishList.objects.get(id=wishlist_id)
            if wishlist.is_allowed_to_edit(user):
                wishlist.delete()
                return DeleteWishList(success=True)
        except WishList.DoesNotExist:
            raise Exception("Invalid wishlist ID.")
        raise Exception("Not authorized to delete this wishlist.")


class UpdateWishList(graphene.Mutation):
    class Arguments:
        wishlist_id = graphene.ID(required=True)
        name = graphene.String()
        visibility = graphene.String()

    wishlist = graphene.Field(WishListType)

    def mutate(self, info, wishlist_id, name=None, visibility=None):
        user = info.context.user
        try:
            wishlist = WishList.objects.get(id=wishlist_id)
            if wishlist.is_allowed_to_edit(user):
                if name:
                    wishlist.name = name
                if visibility:
                    wishlist.visibility = visibility
                wishlist.save()
                return UpdateWishList(wishlist=wishlist)
        except WishList.DoesNotExist:
            raise Exception("Invalid wishlist ID.")
        raise Exception("Not authorized to update this wishlist.")

# Mutations
class WishListMutation(graphene.ObjectType):
    create_wishlist = CreateWishList.Field()
    add_to_wishlist = AddToWishList.Field()
    remove_from_wishlist = RemoveFromWishList.Field()
    delete_wishlist = DeleteWishList.Field()
    update_wishlist = UpdateWishList.Field()
    share_wishlist = ShareWishList.Field()

# Schema
class WishListSchema(graphene.Schema):
    query = WishListQuery
    mutation = WishListMutation
