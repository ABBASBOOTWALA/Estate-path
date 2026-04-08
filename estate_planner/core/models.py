from dataclasses import dataclass, field, asdict
from typing import Optional, List


@dataclass
class DeceasedProfile:
    full_name: str = ""
    date_of_birth: str = ""
    date_of_death: str = ""
    state_of_residence: str = ""
    county: str = ""
    had_will: bool = False
    is_veteran: bool = False
    executor_name: str = ""
    executor_address: str = ""
    executor_city_state_zip: str = ""
    executor_email: str = ""
    executor_phone: str = ""
    social_security_number_last4: str = ""
    estimated_estate_value: str = ""
    has_real_property: bool = False
    has_minor_children: bool = False
    has_business_interests: bool = False
    has_trust: bool = False
    digital_accounts: List[str] = field(default_factory=list)
    financial_accounts: List[str] = field(default_factory=list)
    insurance_policies: List[str] = field(default_factory=list)
    vehicles: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class EstateTask:
    task_id: str = ""
    category: str = ""
    title: str = ""
    institution: str = ""
    description: str = ""
    status: str = "not_started"
    priority: str = "medium"
    deadline: Optional[str] = None
    deadline_rule: str = ""
    documents_needed: List[str] = field(default_factory=list)
    can_auto_generate: bool = False
    template_name: Optional[str] = None
    notes: str = ""
    completed_date: Optional[str] = None
    contact_name: str = ""
    contact_phone: str = ""
    contact_address: str = ""
    contact_url: str = ""

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class GeneratedDocument:
    doc_id: str = ""
    task_id: str = ""
    title: str = ""
    institution: str = ""
    created_at: str = ""
    file_path: str = ""
    template_used: str = ""

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Deadline:
    deadline_id: str = ""
    task_id: str = ""
    title: str = ""
    due_date: str = ""
    days_remaining: int = 0
    legal_basis: str = ""
    consequences_if_missed: str = ""
    is_hard_deadline: bool = True

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ActivityEntry:
    timestamp: str = ""
    action: str = ""
    task_id: str = ""
    description: str = ""

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
