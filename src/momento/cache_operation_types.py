import json
from datetime import datetime
from enum import Enum
from typing import Any, Optional, List, Mapping

from momento_wire_types import cacheclient_pb2 as cache_client_types
from . import _cache_service_errors_converter as error_converter
from . import _momento_logger


class CacheGetStatus(Enum):
    HIT = 1
    MISS = 2


class CacheSetResponse:
    def __init__(self, grpc_set_response: Any, key: bytes, value: bytes):  # type: ignore[misc]
        """Initializes CacheSetResponse to handle gRPC set response.

        Args:
            grpc_set_response: Protobuf based response returned by Scs.
            key (bytes): The value of the key of item that was stored in cache..
            value (bytes): The value of item that was stored in the cache.

        Raises:
            InternalServerError: If server encountered an unknown error while trying to store the item.
        """
        self._value = value
        self._key = key

    def value(self) -> str:
        """Decodes string value set in cache to a utf-8 string."""
        return self._value.decode("utf-8")

    def value_as_bytes(self) -> bytes:
        """Returns byte value set in cache."""
        return self._value

    def key(self) -> str:
        """Decodes key of item set in cache to a utf-8 string."""
        return self._key.decode("utf-8")

    def key_as_bytes(self) -> bytes:
        """Returns key of item stored in cache as bytes."""
        return self._key


class CacheMultiSetResponse:
    def __init__(self, items: Mapping[bytes, bytes]):
        self._items = items

    def items(self) -> Mapping[str, str]:
        return {
            key.decode("utf-8"): value.decode("utf-8")
            for key, value in self._items.items()
        }

    def items_as_bytes(self) -> Mapping[bytes, bytes]:
        return self._items

    def __repr__(self) -> str:
        return f"CacheMultiSetResponse(items={self._items!r})"


class CacheGetResponse:
    def __init__(self, value: bytes, result: CacheGetStatus):
        self._value = value
        self._result = result

    @staticmethod
    def from_grpc_response(grpc_get_response: Any) -> "CacheGetResponse":  # type: ignore[misc]
        """Initializes CacheGetResponse to handle gRPC get response.

        Args:
            grpc_get_response: Protobuf based response returned by Scs.

        Raises:
            InternalServerError: If server encountered an unknown error while trying to retrieve the item.
        """
        value: bytes = grpc_get_response.cache_body  # type: ignore[misc]

        if grpc_get_response.result == cache_client_types.Hit:  # type: ignore[misc]
            result = CacheGetStatus.HIT
        elif grpc_get_response.result == cache_client_types.Miss:  # type: ignore[misc]
            result = CacheGetStatus.MISS
        else:
            _momento_logger.debug(
                f"Get received unsupported ECacheResult: {grpc_get_response.result}"  # type: ignore[misc]
            )
            raise error_converter.convert_ecache_result(
                grpc_get_response.result, grpc_get_response.message, "GET"  # type: ignore[misc]
            )
        return CacheGetResponse(value=value, result=result)

    def value(self) -> Optional[str]:
        """Returns value stored in cache as utf-8 string if there was Hit. Returns None otherwise."""
        if self._result == CacheGetStatus.HIT:
            return self._value.decode("utf-8")
        return None

    def value_as_bytes(self) -> Optional[bytes]:
        """Returns value stored in cache as bytes if there was Hit. Returns None otherwise."""
        if self._result == CacheGetStatus.HIT:
            return self._value
        return None

    def status(self) -> CacheGetStatus:
        """Returns get operation result such as HIT or MISS."""
        return self._result

    def __repr__(self) -> str:
        return f"CacheGetResponse(value={self._value!r}, result={self._result!r})"


class CacheMultiGetResponse:
    def __init__(self, responses: List[CacheGetResponse]):
        self._responses = responses

    def status(self) -> List[CacheGetStatus]:
        return [response.status() for response in self._responses]

    def values(self) -> List[Optional[str]]:
        """Returns list of values as utf-8 string for each Hit. Each item in list is None if was a Miss."""
        return [response.value() for response in self._responses]

    def values_as_bytes(self) -> List[Optional[bytes]]:
        """Returns list of values as bytes for each Hit. Each item in list is None if was a Miss."""
        return [response.value_as_bytes() for response in self._responses]

    def to_list(self) -> List[CacheGetResponse]:
        return self._responses

    def __repr__(self) -> str:
        return f"CacheMultiGetResponse(responses={self._responses!r})"


class CacheDeleteResponse:
    def __init__(self, grpc_create_cache_response: Any):  # type: ignore[misc]
        pass


class CreateCacheResponse:
    def __init__(self, grpc_create_cache_response: Any):  # type: ignore[misc]
        pass


class DeleteCacheResponse:
    def __init__(self, grpc_delete_cache_response: Any):  # type: ignore[misc]
        pass


class CacheInfo:
    def __init__(self, grpc_listed_cache: Any):  # type: ignore[misc]
        """Initializes CacheInfo to handle caches returned from list cache operation.

        Args:
            grpc_listed_cache: Protobuf based response returned by Scs.
        """
        self._name: str = grpc_listed_cache.cache_name  # type: ignore[misc]

    def name(self) -> str:
        """Returns all cache's name."""
        return self._name


class ListCachesResponse:
    def __init__(self, grpc_list_cache_response: Any):  # type: ignore[misc]
        """Initializes ListCacheResponse to handle list cache response.

        Args:
            grpc_list_cache_response: Protobuf based response returned by Scs.
        """
        self._next_token: Optional[str] = (
            grpc_list_cache_response.next_token  # type: ignore[misc]
            if grpc_list_cache_response.next_token != ""  # type: ignore[misc]
            else None
        )
        self._caches = []
        for cache in grpc_list_cache_response.cache:  # type: ignore[misc]
            self._caches.append(CacheInfo(cache))  # type: ignore[misc]

    def next_token(self) -> Optional[str]:
        """Returns next token."""
        return self._next_token

    def caches(self) -> List[CacheInfo]:
        """Returns all caches."""
        return self._caches


class CreateSigningKeyResponse:
    def __init__(self, grpc_create_signing_key_response: Any, endpoint: str):  # type: ignore[misc]
        """Initializes CreateSigningKeyResponse to handle create signing key response.

        Args:
            grpc_create_signing_key_response: Protobuf based response returned by Scs.
        """
        self._key_id: str = json.loads(grpc_create_signing_key_response.key)["kid"]  # type: ignore[misc]
        self._endpoint: str = endpoint
        self._key: str = grpc_create_signing_key_response.key  # type: ignore[misc]
        self._expires_at: datetime = datetime.fromtimestamp(
            grpc_create_signing_key_response.expires_at  # type: ignore[misc]
        )

    def key_id(self) -> str:
        """Returns the id of the signing key"""
        return self._key_id

    def endpoint(self) -> str:
        """Returns the endpoint of the signing key"""
        return self._endpoint

    def key(self) -> str:
        """Returns the JSON string of the key itself"""
        return self._key

    def expires_at(self) -> datetime:
        """Returns the datetime representation of when the key expires"""
        return self._expires_at


class RevokeSigningKeyResponse:
    def __init__(self, grpc_revoke_signing_key_response: Any):  # type: ignore[misc]
        pass


class SigningKey:
    def __init__(self, grpc_listed_signing_key: Any, endpoint: str):  # type: ignore[misc]
        """Initializes SigningKey to handle signing keys returned from list signing keys operation.

        Args:
            grpc_listed_signing_key: Protobuf based response returned by Scs.
        """
        self._key_id: str = grpc_listed_signing_key.key_id  # type: ignore[misc]
        self._expires_at: datetime = datetime.fromtimestamp(
            grpc_listed_signing_key.expires_at  # type: ignore[misc]
        )
        self._endpoint: str = endpoint

    def key_id(self) -> str:
        """Returns the id of the Momento signing key"""
        return self._key_id

    def expires_at(self) -> datetime:
        """Returns the time the key expires"""
        return self._expires_at

    def endpoint(self) -> str:
        """Returns the endpoint of the Momento signing key"""
        return self._endpoint


class ListSigningKeysResponse:
    def __init__(self, grpc_list_signing_keys_response: Any, endpoint: str):  # type: ignore[misc]
        """Initializes ListSigningKeysResponse to handle list signing keys response.

        Args:
            grpc_list_signing_keys_response: Protobuf based response returned by Scs.
        """
        self._next_token: Optional[str] = (
            grpc_list_signing_keys_response.next_token  # type: ignore[misc]
            if grpc_list_signing_keys_response.next_token != ""  # type: ignore[misc]
            else None
        )
        self._signing_keys: List[SigningKey] = [  # type: ignore[misc]
            SigningKey(signing_key, endpoint)  # type: ignore[misc]
            for signing_key in grpc_list_signing_keys_response.signing_key  # type: ignore[misc]
        ]

    def next_token(self) -> Optional[str]:
        """Returns next token."""
        return self._next_token

    def signing_keys(self) -> List[SigningKey]:
        """Returns all signing keys."""
        return self._signing_keys
