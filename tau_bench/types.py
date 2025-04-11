# Copyright Sierra

from pydantic import BaseModel, model_validator
from typing import List, Dict, Any, Optional, Union, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from tau_bench.agents.tool_calling_agent import ToolCallingAgent

RESPOND_ACTION_NAME = "respond"
RESPOND_ACTION_FIELD_NAME = "content"


class Action(BaseModel):
    name: str
    kwargs: Dict[str, Any]


class Task(BaseModel):
    id: Optional[int] = None
    user_id: str
    actions: List[Action]
    instruction: str
    outputs: List[str]


class RewardOutputInfo(BaseModel):
    r_outputs: float
    outputs: Dict[str, bool]


class RewardActionInfo(BaseModel):
    r_actions: float
    gt_data_hash: str


class RewardResult(BaseModel):
    reward: float
    info: Union[RewardOutputInfo, RewardActionInfo]
    actions: List[Action]


class SolveResult(BaseModel):
    reward: float
    write_actions_diff: Optional[Dict[str, Any]] = None
    messages: List[Dict[str, Any]]
    info: Dict[str, Any]
    key_actions: Optional[List[Action]] = None
    raw_messages: Optional[List[Dict[str, Any]]] = None
    node_turns: Optional[List[Dict]] = None
    oai_messages: Optional[List[Dict[str, Any]]] = None
    anthropic_messages: Optional[List[Dict[str, Any]]] = None
    actions_diff: Optional[Dict[str, Any]] = None
    total_cost: Optional[float] = None
    total_user_cost: Optional[float] = None


class EnvInfo(BaseModel):
    task: Task
    source: Optional[str] = None
    user_cost: Optional[float] = None
    reward_info: Optional[RewardResult] = None


class EnvResponse(BaseModel):
    observation: str
    reward: float
    done: bool
    info: EnvInfo


class EnvResetResponse(BaseModel):
    observation: str
    info: EnvInfo


class EnvRunResult(BaseModel):
    task_id: int
    reward: float
    write_actions_diff: Optional[Dict[str, Any]] = None
    actions_diff: Optional[Dict[str, Any]] = None
    info: Dict[str, Any]
    key_actions: Optional[List[Action]] = None
    traj: List[Dict[str, Any]]
    trial: int
    raw_messages: Optional[List[Dict[str, Any]]] = None
    node_turns: Optional[List[Dict]] = None
    oai_messages: Optional[List[Dict[str, Any]]] = None
    anthropic_messages: Optional[List[Dict[str, Any]]] = None
    total_cost: Optional[float] = None
    total_user_cost: Optional[float] = None


class RunConfig(BaseModel):
    model_provider: str
    user_model_provider: str
    model: str
    user_model: str = "gpt-4o"
    num_trials: int = 1
    env: str = "retail"
    agent_strategy: Optional[str] = "tool-calling"
    custom_agent: Optional[Type["ToolCallingAgent"]] = (
        None  # this allows the caller to pass in a custom agent. Ideally, the type would be Agent instead of ToolCallingAgent, but the Agent base interface is too barebone right now.
    )
    temperature: float = 0.0
    task_split: str = "test"
    start_index: int = 0
    end_index: int = -1
    task_ids: Optional[List[int]] = None
    log_dir: str = "results"
    max_concurrency: int = 1
    seed: int = 10
    shuffle: int = 0
    user_strategy: str = "llm"
    few_shot_displays_path: Optional[str] = None

    @model_validator(mode="after")
    def validate_agent(self):
        if not ((self.agent_strategy is None) ^ (self.custom_agent is None)):
            raise ValueError(
                "Exactly one of agent_strategy or custom_agent must be provided"
            )
        return self
