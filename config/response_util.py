from rest_framework.response import Response
from rest_framework import status

def success_response(data=None, status_code=status.HTTP_200_OK):
    """
    Standardized success response.
    """
    return Response({
        "status": "success",
        "data": data
    }, status=status_code)

def error_response(message, status_code):
    """
    Standardized error response.
    """
    return Response({
        "status": "error",
        "error": {
            "code": status_code,
            "message": message
        }
    }, status=status_code)

def validation_error_response(errors, status_code=status.HTTP_400_BAD_REQUEST):
    """
    Standardized validation error response.
    """
    return Response({
        "status": "fail",
        "data": errors
    }, status=status_code)
