from typing import Union, Optional, Callable, Tuple, TypeVar, Awaitable

from momento import _cache_service_errors_converter
from momento import cache_operation_types
from momento import logs
from momento._utilities._data_validation import _validate_ttl, _as_bytes, _validate_cache_name

from momento_wire_types.cacheclient_pb2 import _SetRequest, _SetResponse
from momento_wire_types.cacheclient_pb2 import _GetRequest, _GetResponse
from momento_wire_types.cacheclient_pb2 import _DeleteRequest, _DeleteResponse

TResponse = TypeVar('TResponse')
TGeneratedRequest = TypeVar('TGeneratedRequest')
TGeneratedResponse = TypeVar('TGeneratedResponse')
TExecuteResult = TypeVar('TExecuteResult')
TMomentoResponse = TypeVar('TMomentoResponse')

_logger = logs.logger


def wrap_with_error_handling(
        cache_name: str,
        request_type: str,
        prepare_request_fn: Callable[[], TGeneratedRequest],
        execute_request_fn: Callable[[TGeneratedRequest], TGeneratedResponse],
        response_fn: Callable[[TGeneratedRequest, TGeneratedResponse], TMomentoResponse],
) -> TMomentoResponse:
    _validate_cache_name(cache_name)
    try:
        req = prepare_request_fn()
        resp = execute_request_fn(req)
        return response_fn(req, resp)
    except Exception as e:
        _logger.warning("%s failed with exception: %s", request_type, e)
        raise _cache_service_errors_converter.convert(e)

async def wrap_async_with_error_handling(
        cache_name: str,
        request_type: str,
        prepare_request_fn: Callable[[], TGeneratedRequest],
        execute_request_fn: Callable[[TGeneratedRequest], Awaitable[TGeneratedResponse]],
        response_fn: Callable[[TGeneratedRequest, TGeneratedResponse], TMomentoResponse]
) -> TMomentoResponse:
    _validate_cache_name(cache_name)
    try:
        req = prepare_request_fn()
        resp = await execute_request_fn(req)
        return response_fn(req, resp)
    except Exception as e:
        _logger.warning("%s failed with exception: %s", request_type, e)
        print(f"\n\n\nASYNC '{request_type}' FAILED! {e}")
        raise _cache_service_errors_converter.convert(e)

# def issue_set(
#         cache_name: str,
#         key: Union[str, bytes],
#         value: Union[str, bytes],
#         ttl_seconds: Optional[int],
#         default_ttl_seconds: int,
#         execute_set_request_fn: Callable[[_SetRequest], Tuple[_SetRequest, TResponse]]
# ) -> Tuple[_SetRequest, TResponse]:
#     print("\n\n\n\nCALLING SET\n\n\n\n")
#     _validate_cache_name(cache_name)
#     try:
#         _logger.log(logs.TRACE, "Issuing a set request with key %s", str(key))
#         item_ttl_seconds = default_ttl_seconds if ttl_seconds is None else ttl_seconds
#         _validate_ttl(item_ttl_seconds)
#         set_request = _SetRequest()
#         set_request.cache_key = _as_bytes(key, "Unsupported type for key: ")
#         set_request.cache_body = _as_bytes(value, "Unsupported type for value: ")
#         set_request.ttl_milliseconds = item_ttl_seconds * 1000
#         return set_request, execute_set_request_fn(set_request)
#         # await self._grpc_manager.async_stub().Set(
#         #     set_request,
#         #     metadata=_make_metadata(cache_name),
#         #     timeout=self._default_deadline_seconds,
#         # )
#     except Exception as e:
#         print("WE GOT AN EXCEPTION, YO!")
#         _logger.log(logs.TRACE, "Set failed for %s with response: %s", str(key), e)
#         raise _cache_service_errors_converter.convert(e)


def prepare_set_request(
        key: Union[str, bytes],
        value: Union[str, bytes],
        ttl_seconds: Optional[int],
        default_ttl_seconds: int,
) -> _GetRequest:
    _logger.log(logs.TRACE, "Issuing a set request with key %s", str(key))
    item_ttl_seconds = default_ttl_seconds if ttl_seconds is None else ttl_seconds
    _validate_ttl(item_ttl_seconds)
    set_request = _SetRequest()
    set_request.cache_key = _as_bytes(key, "Unsupported type for key: ")
    set_request.cache_body = _as_bytes(value, "Unsupported type for value: ")
    set_request.ttl_milliseconds = item_ttl_seconds * 1000
    return set_request

def construct_set_response(req: _SetRequest, resp: _SetResponse) -> cache_operation_types.CacheSetResponse:
    _logger.log(logs.TRACE, "Set succeeded for key: %s", str(req.cache_key))
    return cache_operation_types.CacheSetResponse(req.cache_key, req.cache_body)

def prepare_get_request(
        key: Union[str, bytes]
) -> _GetRequest:
    _logger.log(logs.TRACE, "Issuing a Get request with key %s", str(key))
    get_request = _GetRequest()
    get_request.cache_key = _as_bytes(key, "Unsupported type for key: ")
    return get_request


# def issue_get(
#         cache_name: str,
#         key: Union[str, bytes],
#         execute_get_request_fn: Callable[[_GetRequest], Tuple[_GetRequest, TResponse]]
# ) -> Tuple[_GetRequest, TResponse]:
#     _validate_cache_name(cache_name)
#     try:
#         _logger.log(logs.TRACE, "Issuing a get request with key %s", str(key))
#         get_request = _GetRequest()
#         get_request.cache_key = _as_bytes(key, "Unsupported type for key: ")
#         return get_request, execute_get_request_fn(get_request)
#     except Exception as e:
#         _logger.log(logs.TRACE, "Get failed for %s with response: %s", str(key), e)
#         raise _cache_service_errors_converter.convert(e)


def construct_get_response(req: _GetRequest, resp: _GetResponse) -> cache_operation_types.CacheGetResponse:
    _logger.log(logs.TRACE, "Received a get response for %s", str(req.cache_key))
    return cache_operation_types.CacheGetResponse.from_grpc_response(resp)

# def issue_delete(
#         cache_name: str,
#         key: Union[str, bytes],
#         execute_delete_request_fn: Callable[[_DeleteRequest], Tuple[_DeleteRequest, TResponse]]
# ) -> Tuple[_DeleteRequest, TResponse]:
#     _validate_cache_name(cache_name)
#     try:
#         _logger.log(logs.TRACE, "Issuing a delete request with key %s", str(key))
#         delete_request = _DeleteRequest()
#         delete_request.cache_key = _as_bytes(key, "Unsupported type for key: ")
#         return delete_request, execute_delete_request_fn(delete_request)
#     except Exception as e:
#         _logger.debug("Delete failed for %s with response: %s", str(key), e)
#         raise _cache_service_errors_converter.convert(e)

def prepare_delete_request(
        key: Union[str, bytes]
) -> _DeleteRequest:
    _logger.log(logs.TRACE, "Issuing a Delete request with key %s", str(key))
    delete_request = _DeleteRequest()
    delete_request.cache_key = _as_bytes(key, "Unsupported type for key: ")
    return delete_request

def construct_delete_response(req: _DeleteRequest, resp: _DeleteResponse) -> cache_operation_types.CacheDeleteResponse:
    _logger.log(logs.TRACE, "Received a delete response for %s", str(req.cache_key))
    return cache_operation_types.CacheDeleteResponse()
