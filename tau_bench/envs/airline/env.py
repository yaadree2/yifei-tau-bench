# Copyright Sierra

from tau_bench.envs.airline.data import load_data
from tau_bench.envs.airline.rules import RULES
from tau_bench.envs.airline.tools import ALL_TOOLS
from tau_bench.envs.airline.wiki import WIKI
from tau_bench.envs.base import Env
from typing import Any, Dict, Optional, Union
from tau_bench.envs.user import UserStrategy


class MockAirlineDomainEnv(Env):
    def __init__(
        self,
        user_strategy: Union[str, UserStrategy] = UserStrategy.LLM,
        user_model: str = "gpt-4o",
        user_provider: Optional[str] = None,
        task_split: str = "test",
        task_index: Optional[int] = None,
        user_model_kwargs: Optional[Dict[str, Any]] = None,
        logfire_user_completion: bool = False,
    ):
        match task_split:
            case "test":
                from tau_bench.envs.airline.tasks_test import TASKS as tasks
            case "revised_test":
                from tau_bench.envs.airline.revised_tasks_test import TASKS as tasks
            case "dev_test":
                from tau_bench.envs.airline.dev_tasks_test import TASKS as tasks
            case _:
                raise ValueError(f"Unknown task split: {task_split}")
        super().__init__(
            data_load_func=load_data,
            tools=ALL_TOOLS,
            tasks=tasks,
            wiki=WIKI,
            rules=RULES,
            user_strategy=user_strategy,
            user_model=user_model,
            user_provider=user_provider,
            task_index=task_index,
            user_model_kwargs=user_model_kwargs,
            logfire_user_completion=logfire_user_completion,
        )
        self.terminate_tools = ["transfer_to_human_agents"]
