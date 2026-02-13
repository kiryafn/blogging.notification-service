class NotificationError(Exception):
    pass


class EmailSendingFailedError(NotificationError):
    pass


class MessageAlreadyProcessedError(NotificationError):
    pass