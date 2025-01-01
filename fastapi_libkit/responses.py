from typing import Union

from fastapi import status
from pydantic import BaseModel


class ErrorModel(BaseModel):
    detail: Union[str, dict[str, str]]


forbidden_response = {
    status.HTTP_403_FORBIDDEN: {
        "description": "Insufficient permissions",
    },
}


no_content_response = {
    status.HTTP_204_NO_CONTENT: {
        'description': ''
    }
}

missing_token_or_inactive_user_response = {
    status.HTTP_401_UNAUTHORIZED: {
        "description": "Missing token or inactive user.",
    },
}

auth_responses = {**forbidden_response, **missing_token_or_inactive_user_response}




not_found_response = {
    status.HTTP_404_NOT_FOUND: {
        'model': ErrorModel,
    }
}

bad_request_response = {
    status.HTTP_400_BAD_REQUEST: {
        'model': ErrorModel
    }
}

conflict_response = {
    status.HTTP_409_CONFLICT: {
        'model': ErrorModel
    }
}

