from graphene import relay
from graphene_django import DjangoObjectType
import graphene
from oscar.apps.communication.models import (
    Email,
    CommunicationEventType,
    Notification,
)
from django.utils import timezone


# GraphQL Types
class EmailType(DjangoObjectType):
    class Meta:
        model = Email
        fields = ("id", "user", "email", "subject", "body_text", "body_html", "date_sent")
        interfaces = (relay.Node,)


class EmailConnection(relay.Connection):
    class Meta:
        node = EmailType


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
        interfaces = (relay.Node,)


class CommunicationEventTypeConnection(relay.Connection):
    class Meta:
        node = CommunicationEventTypeType


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
        interfaces = (relay.Node,)


class NotificationConnection(relay.Connection):
    class Meta:
        node = NotificationType


# Queries
class CommunicationQuery(graphene.ObjectType):
    emails = relay.ConnectionField(EmailConnection)
    email = relay.Node.Field(EmailType)
    communication_event_types = relay.ConnectionField(CommunicationEventTypeConnection)
    communication_event_type = relay.Node.Field(CommunicationEventTypeType)
    notifications = relay.ConnectionField(NotificationConnection, recipient_id=graphene.ID())
    notification = relay.Node.Field(NotificationType)

    def resolve_emails(self, info, **kwargs):
        return Email.objects.all()

    def resolve_communication_event_types(self, info, **kwargs):
        return CommunicationEventType.objects.all()

    def resolve_notifications(self, info, recipient_id=None, **kwargs):
        if recipient_id:
            return Notification.objects.filter(recipient_id=recipient_id)
        return Notification.objects.all()


# Mutations for Communication
class CreateEmailMutation(relay.ClientIDMutation):
    class Input:
        user_id = graphene.ID(required=True)
        email = graphene.String(required=True)
        subject = graphene.String(required=True)
        body_text = graphene.String()
        body_html = graphene.String()

    email_instance = graphene.Field(EmailType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, user_id, email, subject, body_text=None, body_html=None):
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


class CreateNotificationMutation(relay.ClientIDMutation):
    class Input:
        recipient_id = graphene.ID(required=True)
        sender_id = graphene.ID()
        subject = graphene.String(required=True)
        body = graphene.String(required=True)
        location = graphene.String()

    notification = graphene.Field(NotificationType)

    @classmethod
    def mutate_and_get_payload(cls, root, info, recipient_id, subject, body, sender_id=None, location=None):
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


class MarkNotificationAsReadMutation(relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, root, info, id):
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
    mutation = CommunicationMutation
