# Native Messaging Protocol Specification

## Overview

Communication between the Chrome extension and the Python agent uses
[Chrome Native Messaging](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging).
Messages are length-prefixed JSON over `stdio`.

## Wire Format

Each message on the wire is:

```
[ 4-byte little-endian uint32 length ][ UTF-8 JSON payload ]
```

## Message Envelope

Every JSON payload follows this envelope:

```jsonc
{
  "type": "<MESSAGE_TYPE>",   // discriminator
  "version": "1",             // protocol version
  "timestamp": "ISO-8601",    // sender wall-clock
  "correlation_id": "<uuid>", // ties request → response
  "payload": { ... }          // type-specific data
}
```

## Message Types

| Type               | Direction          | Description                              |
| ------------------ | ------------------ | ---------------------------------------- |
| `HELLO`            | extension → agent  | Handshake; agent replies with `HELLO_ACK`|
| `HELLO_ACK`        | agent → extension  | Confirms agent version & capabilities    |
| `BROWSER_EVENT`    | extension → agent  | Navigation / tab activity                |
| `DOWNLOAD_EVENT`   | extension → agent  | Download state change                    |
| `SCAN_REQUEST`     | extension → agent  | Ask agent to scan a download             |
| `SCAN_RESULT`      | agent → extension  | Risk snapshot for a completed scan       |
| `DECISION`         | agent → extension  | Block / allow / quarantine decision      |
| `ERROR`            | either direction   | Protocol or processing error             |

## HELLO Handshake

The extension sends `HELLO` immediately after connecting. The agent must
respond with `HELLO_ACK` containing its version and supported protocol
version. If the agent does not respond within 5 seconds the extension
treats the connection as failed.

### HELLO Payload

```json
{
  "extension_version": "0.1.0"
}
```

### HELLO_ACK Payload

```json
{
  "agent_version": "0.1.0",
  "protocol_version": "1",
  "capabilities": ["scan", "yara", "provenance"]
}
```

## Versioning

- The `version` field in the envelope is the protocol version (currently `"1"`).
- Breaking changes increment the protocol version.
- Both sides should reject messages with an unsupported protocol version.
