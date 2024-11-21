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


class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = ("id", "name", "description", "slug", "is_public", "full_name")


class ProductType(DjangoObjectType):
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
        )

    categories = graphene.List(CategoryType)

    def resolve_categories(self, info):
        return self.categories.all()


class ProductCategoryType(DjangoObjectType):
    class Meta:
        model = ProductCategory
        fields = ("id", "product", "category")


class ProductRecommendationType(DjangoObjectType):
    class Meta:
        model = ProductRecommendation
        fields = ("id", "primary", "recommendation", "ranking")


class ProductAttributeType(DjangoObjectType):
    class Meta:
        model = ProductAttribute
        fields = ("id", "name", "code", "type", "required", "option_group")


class ProductAttributeValueType(DjangoObjectType):
    class Meta:
        model = ProductAttributeValue
        fields = ("id", "product", "attribute", "value_as_text")


class AttributeOptionGroupType(DjangoObjectType):
    class Meta:
        model = AttributeOptionGroup
        fields = ("id", "name", "code")


class AttributeOptionType(DjangoObjectType):
    class Meta:
        model = AttributeOption
        fields = ("id", "group", "option", "code")


class OptionType(DjangoObjectType):
    class Meta:
        model = Option
        fields = ("id", "name", "type", "required", "option_group")


class ProductImageType(DjangoObjectType):
    class Meta:
        model = ProductImage
        fields = ("id", "product", "original", "caption", "display_order")


# Queries
class CatalogueQuery(graphene.ObjectType):
    all_products = graphene.List(ProductType)
    product_by_id = graphene.Field(ProductType, id=graphene.ID(required=True))
    all_categories = graphene.List(CategoryType)
    category_by_id = graphene.Field(CategoryType, id=graphene.ID(required=True))
    product_classes = graphene.List(ProductClassType)

    def resolve_all_products(self, info):
        return Product.objects.filter(is_public=True)

    def resolve_product_by_id(self, info, id):
        try:
            return Product.objects.get(id=id, is_public=True)
        except Product.DoesNotExist:
            return None

    def resolve_all_categories(self, info):
        return Category.objects.filter(is_public=True)

    def resolve_category_by_id(self, info, id):
        try:
            return Category.objects.get(id=id, is_public=True)
        except Category.DoesNotExist:
            return None

    def resolve_product_classes(self, info):
        return ProductClass.objects.all()

# Mutations for Catalogue
class CreateProductMutation(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        description = graphene.String()
        product_class_id = graphene.ID(required=True)
        is_public = graphene.Boolean(default_value=True)
        is_discountable = graphene.Boolean(default_value=True)

    product = graphene.Field(ProductType)

    def mutate(self, info, title, product_class_id, description=None, is_public=True, is_discountable=True):
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


class UpdateProductMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        title = graphene.String()
        description = graphene.String()
        is_public = graphene.Boolean()
        is_discountable = graphene.Boolean()

    product = graphene.Field(ProductType)

    def mutate(self, info, id, title=None, description=None, is_public=None, is_discountable=None):
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


class DeleteProductMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
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
