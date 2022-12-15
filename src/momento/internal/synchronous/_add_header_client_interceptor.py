import collections
from typing import Callable, List, Union, TypeVar

import grpc

from momento.errors import InvalidArgumentError

RequestType = TypeVar('RequestType')
ResponseType = TypeVar('ResponseType')


class Header:
    once_only_headers = ["agent"]

    def __init__(self, name: str, value: str):
        self.name = name
        self.value = value


class _ClientCallDetails(
    collections.namedtuple(
        "_ClientCallDetails", ("method", "timeout", "metadata", "credentials")
    ),
    grpc.ClientCallDetails,
):
    pass


class AddHeaderClientInterceptor(grpc.UnaryUnaryClientInterceptor):
    are_only_once_headers_sent = False

    def __init__(self, headers: List[Header]):
        self._headers_to_add_once: List[Header] = list(
            filter(lambda header: header.name in header.once_only_headers, headers)
        )
        self.headers_to_add_every_time = list(
            filter(lambda header: header.name not in header.once_only_headers, headers)
        )



#     #
# class _GenericClientInterceptor(grpc.UnaryUnaryClientInterceptor):
#     def __init__(self, interceptor_function: Any):  # type: ignore[misc]
#         self._fn = interceptor_function
#
#     def intercept_unary_unary(  # type: ignore[misc]
#             self,
#             continuation: Any,
#             client_call_details: ClientCallDetails,
#             request: Any,
#     ) -> Any:
#         new_details, new_request_iterator, postprocess = self._fn(
#             client_call_details, iter((request,)), False, False
#         )
#         response = continuation(new_details, next(new_request_iterator))
#         return postprocess(response) if postprocess else response

    def intercept_unary_unary(self,
                              continuation: Callable[[grpc.ClientCallDetails, RequestType], grpc.Call],
                              client_call_details: grpc.ClientCallDetails,
                              request
                              ) -> grpc.Call:

    # async def intercept_unary_unary(
    #     self,
    #     continuation: Callable[
    #         [grpc.aio._interceptor.ClientCallDetails, grpc.aio._typing.RequestType],
    #         grpc.aio._call.UnaryUnaryCall,
    #     ],
    #     client_call_details: grpc.aio._interceptor.ClientCallDetails,
    #     request: grpc.aio._typing.RequestType,
    # ) -> Union[grpc.aio._call.UnaryUnaryCall, grpc.aio._typing.ResponseType]:

        new_client_call_details = sanitize_client_call_details(client_call_details)
        # new_client_call_details = client_call_details

        for header in self.headers_to_add_every_time:
            new_client_call_details.metadata.append((header.name, header.value))

        if not AddHeaderClientInterceptor.are_only_once_headers_sent:
            for header in self._headers_to_add_once:
                new_client_call_details.metadata.append((header.name, header.value))
                AddHeaderClientInterceptor.are_only_once_headers_sent = True

        # return await continuation(new_client_call_details, request)
        return continuation(new_client_call_details, request)


def sanitize_client_call_details(client_call_details: grpc.aio.ClientCallDetails) -> grpc.aio.ClientCallDetails:
    # """
    # Defensive function meant to handle inbound grpc client request objects and make sure we can handle properly
    # when we inject our own metadata onto request object. This was mainly done as temporary fix after we observed
    # ddtrace grpc client interceptor passing client_call_details.metadata as a list instead of a grpc.aio.Metadata
    # object. See this ticket for follow-up actions to come back in and address this longer term:
    #     https://github.com/momentohq/client-sdk-python/issues/149
    # Args:
    #     client_call_details: the original inbound client grpc request we are intercepting
    #
    # Returns: a new client_call_details object with metadata properly initialized to a `grpc.aio.Metadata` object
    # """

    # If no metadata set on passed in client call details then we are first to set, so we should just initialize
    if client_call_details.metadata is None:
        return _ClientCallDetails(
            method=client_call_details.method,
            timeout=client_call_details.timeout,
            metadata=[],
            credentials=client_call_details.credentials,
            # wait_for_ready=client_call_details.wait_for_ready,
        )

    # This is block hit when ddtrace interceptor runs first and sets metadata as a list
    elif isinstance(client_call_details.metadata, list):
        return client_call_details
        # existing_headers = client_call_details.metadata
        # metadata = Metadata()
        # # re-add all existing values to new metadata
        # for md_key, md_value in existing_headers:
        #     metadata.add(md_key, md_value)
        # new_client_call_details = grpc.ClientCallDetails(
        #     method=client_call_details.method,
        #     timeout=client_call_details.timeout,
        #     metadata=metadata,
        #     credentials=client_call_details.credentials,
        #     wait_for_ready=client_call_details.wait_for_ready,
        # )
    # elif isinstance(client_call_details.metadata, grpc.aio.Metadata):
    #     # If  proper grpc `grpc.aio.Metadata()` object is passed just use original object passed and pass back
    #     new_client_call_details = client_call_details
    else:
        # Else we raise exception for now since we don't know how to handle an unknown type
        raise InvalidArgumentError(
            "unexpected grpc client request metadata property passed to interceptor "
            "type=" + str(type(client_call_details.metadata))
        )

    # return new_client_call_details
