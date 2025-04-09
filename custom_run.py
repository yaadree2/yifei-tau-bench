import argparse

import logfire
from tau_bench.agents.tool_calling_agent import *  # noqa: F403, F401
from tau_bench.envs.base import *  # noqa: F403, F401
from tau_bench.run import run
from tau_bench.types import RunConfig

from cashier.model.model_client import ModelClient
from cashier.model.model_util import CustomJSONEncoder
from cashier.model.types import get_default_model_provider_for_model_name
from tau_benchmark.custom_agent import CustomToolCallingAgent

RunConfig.model_rebuild()


def run_with_defaults(args) -> None:
    """
    Wrapper to run the benchmark with sensible defaults
    """
    # Construct command line arguments
    logfire.configure(scrubbing=False, console=False)
    model_provider = get_default_model_provider_for_model_name(args.model)
    ModelClient.initialize()
    config = RunConfig(
        model_provider=str(model_provider).lower(),
        user_model_provider="openrouter",
        model=args.model,
        user_model="openrouter/anthropic/claude-3.5-sonnet",
        num_trials=args.num_trials,
        env="airline",
        agent_strategy=None,
        custom_agent=CustomToolCallingAgent,
        task_split="revised_test",
        log_dir="tau_benchmark/results",
        start_index=args.start_index,
        end_index=args.end_index,
        task_ids=args.task_ids,
        max_concurrency=args.max_concurrency,
        user_strategy="llm",
    )

    with logfire.span(
        "Run session: task_ids={task_ids}, num_trials={num_trials}, max_concurrency={max_concurrency}",
        task_ids=args.task_ids,
        start_index=args.start_index,
        end_index=args.end_index,
        num_trials=args.num_trials,
        max_concurrency=args.max_concurrency,
    ) as span:
        results = run(config, CustomJSONEncoder)

        rewards = sum([r.reward for r in results])
        span.set_attribute("total_completed_count", len(results))
        span.set_attribute("total_successful_count", rewards)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-trials", type=int, default=1)
    parser.add_argument("--model", type=str, default="claude-3-5-sonnet-20241022")
    parser.add_argument(
        "--task-ids",
        type=int,
        nargs="+",
        help="(Optional) run only the tasks with the given IDs",
        default=None,
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=43,
        help="Number of tasks to run in parallel",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--end-index",
        type=int,
        default=-1,
    )

    args = parser.parse_args()
    # Example usage
    run_with_defaults(args=args)
