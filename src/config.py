from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class ThemeTokens:
    accent: str = "#24543D"
    accent_soft: str = "#EAF4EF"
    text: str = "#12211A"
    heading: str = "#0E1B15"
    muted: str = "#4D5E55"
    border: str = "#B8CCC0"
    danger: str = "#7A1F1F"
    warning: str = "#7A4E00"
    success: str = "#1E5C2E"
    logo_file: str = "wheel_logo.png"


@dataclass(frozen=True)
class ReviewRequirednessRules:
    require_adjudication_for_interruptive: bool = True
    require_action_for_interruptive: bool = True
    require_override_reason: bool = True


@dataclass(frozen=True)
class FeatureFlags:
    enable_demo_shortcuts: bool = True
    enable_raw_json_expanders: bool = True
    enable_assignment_matrix: bool = True


@dataclass(frozen=True)
class SameClassRuleToggles:
    high_risk_class_duplication_enabled: bool = True


@dataclass(frozen=True)
class AppConfig:
    default_case_id: str = "case_01"
    default_metric_window: str = "90d"
    default_llm_mode: str = "LLM Assisted"
    default_page: str = "Review Queue"
    theme: ThemeTokens = field(default_factory=ThemeTokens)
    features: FeatureFlags = field(default_factory=FeatureFlags)
    same_class_rules: SameClassRuleToggles = field(default_factory=SameClassRuleToggles)
    review_requiredness: ReviewRequirednessRules = field(default_factory=ReviewRequirednessRules)
    llm_mode_labels: Dict[str, bool] = field(
        default_factory=lambda: {
            "LLM Assisted": True,
            "Hard Coded Functionality": False,
        }
    )


DEFAULT_CONFIG = AppConfig()
