class KernelCityError(Exception):
    pass


class ValidationError(KernelCityError):
    pass


class PathValidationError(ValidationError):
    pass


class ResourceValidationError(ValidationError):
    pass


class ProcessExecutionError(KernelCityError):
    pass

