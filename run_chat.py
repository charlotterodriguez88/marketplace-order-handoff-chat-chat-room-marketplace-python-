from src.marketplace_chat import HandoffRequest, InfraiRealtime, open_order_room


if __name__ == "__main__":
    request = HandoffRequest("order-1042", "seller-7", "buyer-19", "Courier pickup confirmed")
    print(open_order_room(request, InfraiRealtime()))
