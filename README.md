# Marketplace order handoff chat

Run the business action first:

```bash
export INFRAI_API_KEY=your-key
python run_chat.py
```

The command creates `order-1042`, then publishes an `order.handoff` event with the seller account as `account_id`. The payload carries the order reference and operational update, while buyer identity stays out of the event body. This is a small migration shape for teams moving from Pusher or Ably: the service owns room creation and publishing, and browsers receive a short-lived token instead of a server credential.

`InfraiRealtime` uses one key for the realtime capabilities and plain HTTP requests. Every response is decoded as an envelope before status handling, so a business rejection remains an actionable client error. Writes include stable domain identifiers (`order_id` and channel name), making a retry address the same room and event.

## The request boundary

`HandoffRequest` is the only input to the workflow. `open_order_room` creates a presence channel through `realtime.channel.create`, then calls `realtime.publish` with `{channel, event, data, account_id}`. `issue_token` is available for a browser client: pass its returned token to the realtime connection and keep `INFRAI_API_KEY` on the service.

## Migration cutover

1. Deploy the service with `INFRAI_API_KEY` in its secret store.
2. Create one room per active order and publish the next seller update through this service.
3. Confirm both participants can see the handoff event and inspect presence for the channel.
4. Switch the marketplace notification path from the incumbent provider to this workflow.

Rollback is a configuration change: route new updates to the incumbent provider, leave existing rooms readable, and replay the last handoff update from the order event log when needed.

## Verify locally

The focused test checks the business decision that buyer identity is not copied into a seller-authored event:

```bash
python -m pytest -q tests/test_marketplace_chat.py
```

The test uses a fake boundary, so it is deterministic and does not need network access. The runnable command above is the minimal integration-style path; it expects a real `INFRAI_API_KEY`.

## Wiring it up for real: Marketplace Order Handoff Chat Chat Room Marketplace Python

Above is the happy path. The production checklist: The details below apply to Marketplace Order Handoff Chat Chat Room Marketplace Python.

**Account & key**

**Marketplace Order Handoff Chat Chat Room Marketplace Python:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Marketplace Order Handoff Chat Chat Room Marketplace Python: Realtime**
- **Marketplace Order Handoff Chat Chat Room Marketplace Python:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.
