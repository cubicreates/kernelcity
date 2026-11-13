from pathlib import Path
from typing import Iterable, List, Optional

from RES.PHASE_4_TESTING.error_handling import PathValidationError, ValidationError


class InputValidator:
    @staticmethod
    def require_non_empty(value: str, field_name: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValidationError(f"{field_name} cannot be empty.")
        return cleaned

    @staticmethod
    def require_int(value: object, field_name: str, minimum: Optional[int] = None, maximum: Optional[int] = None) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"{field_name} must be an integer.") from exc
        if minimum is not None and parsed < minimum:
            raise ValidationError(f"{field_name} must be >= {minimum}.")
        if maximum is not None and parsed > maximum:
            raise ValidationError(f"{field_name} must be <= {maximum}.")
        return parsed

    @staticmethod
    def require_float(value: object, field_name: str, minimum: Optional[float] = None, maximum: Optional[float] = None) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"{field_name} must be a number.") from exc
        if minimum is not None and parsed < minimum:
            raise ValidationError(f"{field_name} must be >= {minimum}.")
        if maximum is not None and parsed > maximum:
            raise ValidationError(f"{field_name} must be <= {maximum}.")
        return parsed

    @staticmethod
    def require_choice(value: str, allowed: Iterable[str], field_name: str) -> str:
        allowed_list = list(allowed)
        if value not in allowed_list:
            raise ValidationError(f"{field_name} must be one of: {', '.join(allowed_list)}.")
        return value

    @staticmethod
    def validate_safe_path(raw_path: str, allowed_roots: List[Path], must_exist: bool = False) -> Path:
        cleaned = InputValidator.require_non_empty(raw_path, "Path")
        candidate = Path(cleaned)
        if not candidate.is_absolute():
            candidate = allowed_roots[0] / candidate
        resolved = candidate.resolve()
        is_allowed = any(
            resolved == root.resolve() or root.resolve() in resolved.parents
            for root in allowed_roots
        )
        if not is_allowed:
            raise PathValidationError(f"Path '{resolved}' is outside approved project directories.")
        if must_exist and not resolved.exists():
            raise PathValidationError(f"Path '{resolved}' does not exist.")
        return resolved

    @staticmethod
    def validate_int_vector(raw_values: List[object], expected_len: int, field_name: str, allow_zero: bool = True) -> List[int]:
        if len(raw_values) != expected_len:
            raise ValidationError(f"{field_name} must contain exactly {expected_len} values.")
        minimum = 0 if allow_zero else 1
        return [InputValidator.require_int(val, f"{field_name}[{idx}]", minimum=minimum) for idx, val in enumerate(raw_values)]

