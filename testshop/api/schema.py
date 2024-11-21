import graphene
from .queries import Query
from .mutations import Mutation

# Define the GraphQL schema
schema = graphene.Schema(query=Query, mutation=Mutation)