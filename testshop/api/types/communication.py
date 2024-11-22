from graphene_django import DjangoObjectType
import graphene
from oscar.apps.communication.models import (
    Email,
    CommunicationEventType,
    Notification,
)


# GraphQL Types
class EmailType(DjangoObjectType):
    class Meta:
        model = Email
        fields = ("id", "user", "email", "subject", "body_text", "body_html", "date_sent")


class CommunicationEventTypeType(DjangoObjectType):
    class Meta:
        model = CommunicationEventType
        fields = (
            "id",
            "code",
            "name",
            "category",
            "email_subject_template",
            "email_body_template",
            "email_body_html_template",
            "sms_template",
            "date_created",
            "date_updated",
        )


class NotificationType(DjangoObjectType):
    class Meta:
        model = Notification
        fields = (
            "id",
            "recipient",
            "sender",
            "subject",
            "body",
            "location",
            "date_sent",
            "date_read",
        )


# Queries
class CommunicationQuery(graphene.ObjectType):
    emails = graphene.List(EmailType)
    email = graphene.Field(EmailType, id=graphene.ID(required=True))
    communication_event_types = graphene.List(CommunicationEventTypeType)
    communication_event_type = graphene.Field(
        CommunicationEventTypeType, id=graphene.ID(required=True)
    )
    notifications = graphene.List(NotificationType, recipient_id=graphene.ID())
    notification = graphene.Field(NotificationType, id=graphene.ID(required=True))

    def resolve_emails(self, info):
        return Email.objects.all()

    def resolve_email(self, info, id):
        try:
            return Email.objects.get(id=id)
        except Email.DoesNotExist:
            return None

    def resolve_communication_event_types(self, info):
        return CommunicationEventType.objects.all()

    def resolve_communication_event_type(self, info, id):
        try:
            return CommunicationEventType.objects.get(id=id)
        except CommunicationEventType.DoesNotExist:
            return None

    def resolve_notifications(self, info, recipient_id=None):
        if recipient_id:
            return Notification.objects.filter(recipient_id=recipient_id)
        return Notification.objects.all()

    def resolve_notification(self, info, id):
        try:
            return Notification.objects.get(id=id)
        except Notification.DoesNotExist:
            return None

# Mutations for Communication
class CreateEmailMutation(graphene.Mutation):
    class Arguments:
        user_id = graphene.ID(required=True)
        email = graphene.String(required=True)
        subject = graphene.String(required=True)
        body_text = graphene.String()
        body_html = graphene.String()

    email_instance = graphene.Field(EmailType)

    def mutate(self, info, user_id, email, subject, body_text=None, body_html=None):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to send an email.")

        email_instance = Email.objects.create(
            user_id=user_id,
            email=email,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
        )
        return CreateEmailMutation(email_instance=email_instance)


class CreateNotificationMutation(graphene.Mutation):
    class Arguments:
        recipient_id = graphene.ID(required=True)
        sender_id = graphene.ID()
        subject = graphene.String(required=True)
        body = graphene.String(required=True)
        location = graphene.String()

    notification = graphene.Field(NotificationType)

    def mutate(self, info, recipient_id, subject, body, sender_id=None, location=None):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to create a notification.")

        notification = Notification.objects.create(
            recipient_id=recipient_id,
            sender_id=sender_id,
            subject=subject,
            body=body,
            location=location,
        )
        return CreateNotificationMutation(notification=notification)


class MarkNotificationAsReadMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication required to update a notification.")

        try:
            notification = Notification.objects.get(id=id, recipient=user)
        except Notification.DoesNotExist:
            raise Exception("Notification not found or not accessible.")

        notification.date_read = timezone.now()
        notification.save()
        return MarkNotificationAsReadMutation(success=True)

# Mutations
class CommunicationMutation(graphene.ObjectType):
    create_email = CreateEmailMutation.Field()
    create_notification = CreateNotificationMutation.Field()
    mark_notification_as_read = MarkNotificationAsReadMutation.Field()

# Schema
class CommunicationSchema(graphene.Schema):
    query = CommunicationQuery
