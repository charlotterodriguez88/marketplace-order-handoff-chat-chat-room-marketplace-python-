from src.marketplace_chat import HandoffRequest, open_order_room


class FakeRealtime:
    def __init__(self):
        self.calls = []

    def create_channel(self, channel):
        self.calls.append(("create", channel))
        return {"ok": True}

    def publish(self, channel, event, data, account_id):
        self.calls.append(("publish", channel, event, data, account_id))
        return {"ok": True}


def test_handoff_room_contains_order_and_omits_buyer_identity():
    fake = FakeRealtime()
    result = open_order_room(HandoffRequest("42", "seller-7", "buyer-9", "Ready"), fake)
    assert result == {"channel": "order-42", "event": "order.handoff", "published": True}
    assert fake.calls[1][3] == {"order_id": "42", "update": "Ready"}
    assert "buyer-9" not in fake.calls[1][3].values()
