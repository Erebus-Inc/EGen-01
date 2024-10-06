from enum import Enum


class responseSignals(Enum):
    FILE_VALIDATED_SUCCESS = "File validation successful"
    FILE_TYPE_NOT_SUPPORTED = "File is not allowed to be uploaded the type is not supported"
    FILE_SIZE_EXCEEDED = "File is too large to be uploaded "
    FILE_UPLOAD_FAILED = "File upload failed"
    FILE_UPLOAD_SUCCESSFULLY = "File uploaded successfully."
    FILE_NOT_FOUND = "File not found"
    PROJECT_NOT_FOUND = "Project not found"
    USER_NOT_FOUND = "User not found"
    USER_ALREADY_EXISTS = "User already exists"
    PROJECT_ALREADY_EXISTS = "Project already exists"
    INVALID_CREDENTIALS = "Invalid credentials"
    FORBIDDEN_ACCESS = "Forbidden access"
    INCORRECT_PASSWORD = "Incorrect password"
    USER_UPDATED_SUCCESSFULLY = "User updated successfully"
    PROJECT_UPDATED_SUCCESSFULLY = "Project updated successfully"