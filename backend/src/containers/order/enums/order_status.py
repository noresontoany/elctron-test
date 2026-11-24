from enum import StrEnum


class OrderStatus(StrEnum):
    QUEUED = "queued"
    REPAIR = "repair"
    READY = "ready"
    DELIVERED = "delivered"
