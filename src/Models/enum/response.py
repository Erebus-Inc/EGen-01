from enum import Enum


class responseSignals(Enum):
    FILE_VALIDATED_SUCCESS = "File validation successful"
    FILE_TYPE_NOT_SUPPORTED = "File is not allowed to be uploaded the type is not supported"
    FILE_SIZE_EXCEEDED = "File is too large to be uploaded "
    FILE_UPLOAD_FAILED = "File upload failed"
    UPLOAD_SUCCESSFULLY = "File uploaded successfully."
    FILE_NOT_FOUND = "File not found"