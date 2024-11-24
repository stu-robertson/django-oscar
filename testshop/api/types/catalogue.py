from graphene import relay
from graphene_django import DjangoObjectType
import graphene
from oscar.apps.catalogue.models import (
    Product,
    ProductClass,
    Category,
    ProductCategory,
    ProductRecommendation,
    ProductAttribute,
    ProductAttributeValue,
    AttributeOptionGroup,
    AttributeOption,
    Option,
    ProductImage,
)


# GraphQL Types
class ProductClassType(DjangoObjectType):
    class Meta:
        model = ProductClass
        fields = ("id", "name", "slug", "requires_shipping", "track_stock", "options")
        interfaces = (relay.Node,)


class ProductClassConnection(relay.Connection):
    class Meta:
        node = ProductClassType


class CategoryType(DjangoObjectType):
    full_slug = graphene.String()
    public_children = relay.ConnectionField(lambda: CategoryConnection)
    has_children = graphene.Boolean()

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "code",
            "description",
            "slug",
            "is_public",
            "full_name",
            "meta_title",
            "meta_description",
            "image",
        )
        interfaces = (relay.Node,)

    def resolve_full_slug(self, info):
        return self.full_slug

    def resolve_public_children(self, info, **kwargs):
        return self.get_children().filter(is_public=True)

    def resolve_has_children(self, info):
        return self.get_num_children() > 0


class CategoryConnection(relay.Connection):
    class Meta:
        node = CategoryType


class ProductType(DjangoObjectType):
    is_standalone = graphene.Boolean()
    is_parent = graphene.Boolean()
    is_child = graphene.Boolean()
    parent = graphene.Field(lambda: ProductType)
    children = relay.ConnectionField(lambda: ProductConnection)
    primary_image = graphene.String()
    rating = graphene.Float()
    attribute_summary = graphene.String()
    recommended_products = relay.ConnectionField(lambda: ProductConnection)
    categories = relay.ConnectionField(CategoryConnection)

    class Meta:
        model = Product
        fields = (
            "id",
            "title",
            "description",
            "product_class",
            "categories",
            "is_public",
            "date_created",
            "date_updated",
            "is_discountable",
            "upc",
            "structure",
        )
        interfaces = (relay.Node,)

    def resolve_is_standalone(self, info):
        return self.is_standalone

    def resolve_is_parent(self, info):
        return self.is_parent

    def resolve_is_child(self, info):
        return self.is_child

    def resolve_parent(self, info):
        return self.parent if self.is_child else None

    def resolve_children(self, info, **kwargs):
        return self.children.filter(is_public=True) if self.is_parent else []

    def resolve_primary_image(self, info):
        image = self.primary_image()
        return image.original.url if image else None

    def resolve_rating(self, info):
        return self.rating

    def resolve_attribute_summary(self, info):
        return self.attribute_summary

    def resolve_recommended_products(self, info, **kwargs):
        return self.recommended_products.all()

    def resolve_categories(self, info, **kwargs):
        return self.categories.all()


class ProductConnection(relay.Connection):
    class Meta:
        node = ProductType


# Other Types and Connections
class ProductCategoryType(DjangoObjectType):
    class Meta:
        model = ProductCategory
        fields = ("id", "product", "category")
        interfaces = (relay.Node,)


class ProductRecommendationType(DjangoObjectType):
    class Meta:
        model = ProductRecommendation
        fields = ("id", "primary", "recommendation", "ranking")
        interfaces = (relay.Node,)


class ProductAttributeType(DjangoObjectType):
    class Meta:
        model = ProductAttribute
        fields = ("id", "name", "code", "type", "required", "option_group")
        interfaces = (relay.Node,)


class ProductAttributeValueType(DjangoObjectType):
    class Meta:
        model = ProductAttributeValue
        fields = ("id", "product", "attribute", "value_as_text")
        interfaces = (relay.Node,)


class AttributeOptionGroupType(DjangoObjectType):
    class Meta:
        model = AttributeOptionGroup
        fields = ("id", "name", "code")
        interfaces = (relay.Node,)


class AttributeOptionType(DjangoObjectType):
    class Meta:
        model = AttributeOption
        fields = ("id", "group", "option", "code")
        interfaces = (relay.Node,)


class OptionType(DjangoObjectType):
    class Meta:
        model = Option
        fields = ("id", "name", "type", "required", "option_group")
        interfaces = (relay.Node,)


class ProductImageType(DjangoObjectType):
    class Meta:
        model = ProductImage
        fields = ("id", "product", "original", "caption", "display_order")
        interfaces = (relay.Node,)


# Queries
class CatalogueQuery(graphene.ObjectType):
    products = relay.ConnectionField(ProductConnection)
    product = relay.Node.Field(ProductType)
    categories = relay.ConnectionField(CategoryConnection)
    category = relay.Node.Field(CategoryType)
    product_classes = relay.ConnectionField(ProductClassConnection)

    def resolve_products(self, info, **kwargs):
        return Product.objects.filter(is_public=True)

    def resolve_categories(self, info, **kwargs):
        return Category.objects.filter(is_public=True)

    def resolve_product_classes(self, info, **kwargs):
        return ProductClass.objects.all()


# Mutations for Catalogue
class CreateProductMutation(relay.ClientIDMutation):
    class Input:
        title = graphene.String(required=True)
        description = graphene.String()
        product_class_id = graphene.ID(required=True)
        is_public = graphene.Boolean(default_value=True)
        is_discountable = graphene.Boolean(default_value=True)

    product = graphene.Field(ProductType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, title, product_class_id, description=None, is_public=True, is_discountable=True):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to create a product.")

        try:
            product_class = ProductClass.objects.get(id=product_class_id)
        except ProductClass.DoesNotExist:
            raise Exception("Product class not found.")

        product = Product.objects.create(
            title=title,
            description=description,
            product_class=product_class,
            is_public=is_public,
            is_discountable=is_discountable,
        )
        return CreateProductMutation(product=product)


class UpdateProductMutation(relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)
        title = graphene.String()
        description = graphene.String()
        is_public = graphene.Boolean()
        is_discountable = graphene.Boolean()

    product = graphene.Field(ProductType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, id, title=None, description=None, is_public=None, is_discountable=None):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to update a product.")

        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist:
            raise Exception("Product not found.")

        if title is not None:
            product.title = title
        if description is not None:
            product.description = description
        if is_public is not None:
            product.is_public = is_public
        if is_discountable is not None:
            product.is_discountable = is_discountable

        product.save()
        return UpdateProductMutation(product=product)


class DeleteProductMutation(relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, id):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to delete a product.")

        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist:
            raise Exception("Product not found.")

        product.delete()
        return DeleteProductMutation(success=True)


# Mutations
class CatalogueMutation(graphene.ObjectType):
    create_product = CreateProductMutation.Field()
    update_product = UpdateProductMutation.Field()
    delete_product = DeleteProductMutation.Field()


# Schema
class CatalogueSchema(graphene.Schema):
    query = CatalogueQuery
    mutation = CatalogueMutation
