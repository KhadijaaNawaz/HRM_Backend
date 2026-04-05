"""
Custom exception handler for REST Framework.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Customize the error response
        custom_response_data = {
            'error': True,
            'message': str(exc),
            'status_code': response.status_code,
        }

        # Add detail field if available
        if hasattr(response.data, 'get'):
            if 'detail' in response.data:
                custom_response_data['detail'] = response.data['detail']
            # Add validation errors if any
            if isinstance(response.data, dict):
                for key, value in response.data.items():
                    if key != 'detail' and isinstance(value, list):
                        custom_response_data[key] = value

        response.data = custom_response_data

    return response
