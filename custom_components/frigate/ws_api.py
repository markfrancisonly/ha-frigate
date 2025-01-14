"""Frigate HTTP views."""
from __future__ import annotations

import logging

import voluptuous as vol

from custom_components.frigate.api import FrigateApiClient, FrigateApiClientError
from custom_components.frigate.views import get_client_for_frigate_instance_id
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant

_LOGGER: logging.Logger = logging.getLogger(__name__)


def async_setup(hass: HomeAssistant) -> None:
    """Set up the recorder websocket API."""
    websocket_api.async_register_command(hass, ws_retain_event)
    websocket_api.async_register_command(hass, ws_get_recordings)
    websocket_api.async_register_command(hass, ws_get_recordings_summary)


def _get_client_or_send_error(
    hass: HomeAssistant,
    instance_id: str,
    msg_id: int,
    connection: websocket_api.ActiveConnection,
) -> FrigateApiClient | None:
    """Get the API client or send an error that it cannot be found."""
    client = get_client_for_frigate_instance_id(hass, instance_id)
    if client is None:
        connection.send_error(
            msg_id,
            websocket_api.const.ERR_NOT_FOUND,
            f"Unable to find Frigate instance with ID: {instance_id}",
        )
        return None
    return client


@websocket_api.websocket_command(
    {
        vol.Required("type"): "frigate/event/retain",
        vol.Required("instance_id"): str,
        vol.Required("event_id"): str,
        vol.Required("retain"): bool,
    }
)  # type: ignore[misc]
@websocket_api.async_response  # type: ignore[misc]
async def ws_retain_event(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Un/Retain an event."""
    client = _get_client_or_send_error(hass, msg["instance_id"], msg["id"], connection)
    if not client:
        return
    try:
        connection.send_result(
            msg["id"], await client.async_retain(msg["event_id"], msg["retain"])
        )
    except FrigateApiClientError:
        connection.send_error(
            msg["id"],
            "frigate_error",
            f"API error whilst un/retaining event {msg['event_id']} "
            f"for Frigate instance {msg['instance_id']}",
        )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "frigate/recordings/get",
        vol.Required("instance_id"): str,
        vol.Required("camera"): str,
        vol.Optional("after"): int,
        vol.Optional("before"): int,
    }
)  # type: ignore[misc]
@websocket_api.async_response  # type: ignore[misc]
async def ws_get_recordings(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Get recordings for a camera."""
    client = _get_client_or_send_error(hass, msg["instance_id"], msg["id"], connection)
    if not client:
        return
    try:
        connection.send_result(
            msg["id"],
            await client.async_get_recordings(
                msg["camera"], msg.get("after"), msg.get("before")
            ),
        )
    except FrigateApiClientError:
        connection.send_error(
            msg["id"],
            "frigate_error",
            f"API error whilst retrieving recordings for camera {msg['camera']} "
            f"for Frigate instance {msg['instance_id']}",
        )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "frigate/recordings/summary",
        vol.Required("instance_id"): str,
        vol.Required("camera"): str,
    }
)  # type: ignore[misc]
@websocket_api.async_response  # type: ignore[misc]
async def ws_get_recordings_summary(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Get recordings summary for a camera."""
    client = _get_client_or_send_error(hass, msg["instance_id"], msg["id"], connection)
    if not client:
        return
    try:
        connection.send_result(
            msg["id"], await client.async_get_recordings_summary(msg["camera"])
        )
    except FrigateApiClientError:
        connection.send_error(
            msg["id"],
            "frigate_error",
            f"API error whilst retrieving recordings summary for camera "
            f"{msg['camera']} for Frigate instance {msg['instance_id']}",
        )
