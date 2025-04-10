# Copyright Sierra

import json
from typing import Optional

import logfire
from deepdiff import DeepDiff
from redis_util import connect_to_redis, push_assistant_to_redis, push_to_redis_final_reward, push_user_to_redis
from tau_bench.agents.tool_calling_agent import ToolCallingAgent
from tau_bench.envs.base import Env
from tau_bench.types import RESPOND_ACTION_NAME, Action, SolveResult

from cashier.agent_executor import AgentExecutor
from cashier.model.model_args import ModelArgs
from cashier.model.model_completion import Model
from cashier.model.types import MessageFormat, ModelAPI
from tau_benchmark.schema.request_graph_schema import AIRLINE_REQUEST_GRAPH
from tau_benchmark.util import BLACKLISTED_TOOLS, TURN_TYPES
from pydantic_evals.otel._context_in_memory_span_exporter import context_subtree
import json
from cashier.model.cost import compute_token_cost
import uuid

USED_IDS = set()


def generate_unique_id():
    while True:
        new_id = str(uuid.uuid4())
        if new_id not in USED_IDS:
            USED_IDS.add(new_id)
            return new_id


WRITE_TOOL_NAMES = [
    "update_reservation_baggages",
    "update_reservation_flights",
    "update_reservation_passengers",
    "book_reservation",
    "cancel_reservation",
]

TASK_ID_TO_MAX_LENGTH = {
    0: 100,
    1: 125,
    2: 75,
    3: 95,
    4: 90,
    5: 105,
    6: 95,
    7: 50,
    8: 155,
    9: 100,
    10: 105,
    11: 45,
    12: 65,
    13: 68,
    14: 90,
    15: 55,
    16: 85,
    17: 45,
    18: 40,
    19: 45,
    20: 36,
    21: 48,
    22: 40,
    23: 92,
    24: 45,
    25: 105,
    26: 85,
}


def compute_token_attributes_for_agent(llm_spans):
    total_output_tokens = 0
    total_input_tokens = 0
    total_cost = 0
    for llm_span in llm_spans:
        response_data = json.loads(llm_span.attributes["response_data"])
        request_data = json.loads(llm_span.attributes["request_data"])
        output_tokens = response_data["usage"]["completion_tokens"]
        input_tokens = response_data["usage"]["prompt_tokens"]
        total_output_tokens += output_tokens
        total_input_tokens += input_tokens
        total_cost += compute_token_cost(
            request_data["model"], input_tokens, output_tokens
        )

    return total_output_tokens, total_input_tokens, total_cost


def compute_token_attributes_for_user(llm_spans):
    total_output_tokens = 0
    total_input_tokens = 0
    total_cost = 0
    for llm_span in llm_spans:
        completion = json.loads(llm_span.attributes["completion"])
        output_tokens = completion["usage"]["completion_tokens"]
        input_tokens = completion["usage"]["prompt_tokens"]
        total_output_tokens += output_tokens
        total_input_tokens += input_tokens
        total_cost += compute_token_cost(
            completion["model"], input_tokens, output_tokens
        )

    return total_output_tokens, total_input_tokens, total_cost


def compute_cost_attributes(tree, parent_span):
    agent_llm_spans = tree.find({"has_attributes": {"logfire.tags": ("LLM",)}})
    total_output_tokens, total_input_tokens, total_cost = (
        compute_token_attributes_for_agent(agent_llm_spans)
    )
    parent_span.set_attribute("total_output_tokens", total_output_tokens)
    parent_span.set_attribute("total_input_tokens", total_input_tokens)
    parent_span.set_attribute("total_cost", total_cost)

    user_llm_spans = tree.find({"has_attributes": {"logfire.tags": ("CustomerLLM",)}})
    total_output_tokens, total_input_tokens, total_user_cost = (
        compute_token_attributes_for_user(user_llm_spans)
    )
    parent_span.set_attribute("total_USER_output_tokens", total_output_tokens)
    parent_span.set_attribute("total_USER_input_tokens", total_input_tokens)
    parent_span.set_attribute("total_USER_cost", total_user_cost)
    return total_cost, total_user_cost


class CustomToolCallingAgent(ToolCallingAgent):

    def build_tool_fn_registry(
        self,
        expected_task_action_names,
        actual_task_actions,
        actual_write_task_actions,
        env,
    ):
        def wrapper(tool_name, fn):
            def wrapped_fn(*args, **kwargs):
                if (
                    tool_name in expected_task_action_names
                    or tool_name in WRITE_TOOL_NAMES
                ):
                    action = Action(name=tool_name, kwargs=kwargs)
                    actual_task_actions.append(action)
                    if tool_name in WRITE_TOOL_NAMES:
                        actual_write_task_actions.append(action)
                return fn(data=env.data, *args, **kwargs)

            return wrapped_fn

        return {
            tool: wrapper(tool, env.tools_map[tool].invoke)
            for tool in env.tools_map.keys()
            if tool not in BLACKLISTED_TOOLS
        }

    def solve(
        self, env: Env, task_index: Optional[int] = None, max_num_steps: int = 160
    ) -> SolveResult:
        redis_conn = connect_to_redis(False)
        UUID = generate_unique_id()

        user_model = env.user.model
        expected_task_actions = env.task.actions
        expected_task_action_names = [action.name for action in expected_task_actions]
        expected_write_task_actions = [
            action
            for action in expected_task_actions
            if action.name in WRITE_TOOL_NAMES
        ]

        actual_task_actions = []
        actual_write_task_actions = []
        tool_fn_registry = self.build_tool_fn_registry(
            expected_task_action_names,
            actual_task_actions,
            actual_write_task_actions,
            env,
        )
        reward = 0.0

        with logfire.span(
            "Task_id {task_index}, ass_model: {ass_model}, user_model: {user_model}",
            task_index=task_index,
            ass_model=self.model,
            user_model=user_model,
            uuid=UUID,
        ) as span:
            with context_subtree() as tree:
                env_reset_res = env.reset(task_index=task_index)
                obs = env_reset_res.observation
                info = env_reset_res.info.model_dump()

                max_length = TASK_ID_TO_MAX_LENGTH.get(task_index, max_num_steps)
                AE = AgentExecutor(
                    False,
                    True,
                    AIRLINE_REQUEST_GRAPH,
                )
                AE.graph.benchmark_tool_registry = tool_fn_registry
                AE.graph.blacklist_tool_names = BLACKLISTED_TOOLS

                AE.add_user_turn(obs)
                push_user_to_redis(redis_conn, task_index, UUID, obs)

                full_message_dicts = AE.TC.model_api_format_to_message_manager[
                    (ModelAPI.OPENAI, MessageFormat.MANY_SYSTEM_LAST_NODE_PROMPT)
                ].full_message_dicts
                try:
                    for i in range(max_length):
                        model_completion = self.get_model_completion(AE)
                        action = message_to_action(model_completion)
                        AE.add_assistant_turn(model_completion)
                        push_assistant_to_redis(
                            redis_conn,
                            task_index,
                            UUID,
                            AE.get_redis_assistant_turns()
                        )

                        need_user_input = AE.need_user_input
                        env_response = env.step(
                            action,
                            can_do_user_step=need_user_input,
                            can_do_tool_execution=False,
                        )
                        reward = env_response.reward
                        info = {**info, **env_response.info.model_dump()}

                        if need_user_input:
                            AE.add_user_turn(env_response.observation)
                            push_user_to_redis(
                                redis_conn,
                                task_index,
                                UUID,
                                env_response.observation,
                            )
                        else:
                            AE.custom_benchmark_check()

                        if env_response.done:
                            break
                    logfire.info("DONE with reward {reward}", reward=reward)
                    if i == max_length - 1:
                        logfire.error("Max length reached")
                except Exception as e:
                    logfire.exception(f"Exception: {e}")
                    raise e
                finally:
                    write_actions_diff, actions_diff = self.calculate_span_attributes(
                        span,
                        expected_task_actions,
                        expected_write_task_actions,
                        actual_task_actions,
                        actual_write_task_actions,
                        full_message_dicts,
                        reward,
                        user_model,
                        task_index,
                    )

                    push_to_redis_final_reward(redis_conn, UUID, reward)

            total_cost, total_user_cost = compute_cost_attributes(tree, span)

        turns = AE.TC.turns
        oai_messages = []
        raw_messages = []
        anthropic_messages = []
        for turn in turns:
            if isinstance(turn, TURN_TYPES):
                oai_messages.extend(turn.build_oai_messages())
            raw_messages.extend(turn.build_oai_messages())
            anthropic_messages.extend(turn.build_anthropic_messages())

        return SolveResult(
            reward=reward,
            write_actions_diff=write_actions_diff,
            info=info,
            key_actions=actual_task_actions,
            messages=AE.TC.model_api_format_to_message_manager[
                (ModelAPI.OPENAI, MessageFormat.MANY_SYSTEM_LAST_NODE_PROMPT)
            ].conversation_dicts,
            raw_messages=raw_messages,
            node_turns=[turn_dump(node_turn) for node_turn in AE.TC.turns],
            anthropic_messages=anthropic_messages,
            oai_messages=oai_messages,
            actions_diff=actions_diff,
            total_cost=total_cost,
            total_user_cost=total_user_cost,
        )

    def calculate_span_attributes(
        self,
        span,
        expected_task_actions,
        expected_write_task_actions,
        actual_task_actions,
        actual_write_task_actions,
        full_message_dicts,
        reward,
        user_model,
        task_index,
    ):
        write_actions_diff = DeepDiff(
            expected_write_task_actions,
            actual_write_task_actions,
        )
        write_actions_diff = json.loads(write_actions_diff.to_json())
        write_actions_diff_no_order = DeepDiff(
            expected_write_task_actions,
            actual_write_task_actions,
            ignore_order=True,
        )
        write_actions_diff_no_order = json.loads(write_actions_diff_no_order.to_json())
        actions_diff = DeepDiff(expected_task_actions, actual_task_actions)
        actions_diff = json.loads(actions_diff.to_json())
        span.set_attribute("actions_diff", actions_diff)
        span.set_attribute("actions_WRITE_diff", write_actions_diff)
        span.set_attribute("actions_WRITE_NO_ORDER_diff", write_actions_diff_no_order)
        span.set_attribute("expected_actions", expected_task_actions)
        span.set_attribute("actual_actions", actual_task_actions)
        span.set_attribute(
            "full_message_dict",
            full_message_dicts,
        )
        span.set_attribute(
            "full_message_dict_length",
            len(full_message_dicts),
        )
        span.set_attribute("reward", reward)
        span.message = f"Task_id {task_index}, reward: {reward}, ass_model: {self.model}, user_model: {user_model}"
        return write_actions_diff, actions_diff

    def get_model_completion(self, AE):
        model_completion = None
        retries = 3
        model_args = ModelArgs(
            **{
                "model_name": self.model,
                "stream": False,
                "temperature": self.temperature,
                **AE.get_model_completion_kwargs(),
            }
        )
        temp_message_list = None
        message_manager = (
            model_args.message_provider.model_api_format_to_message_manager[
                (model_args.model_api, model_args.message_format)
            ]
        )
        while (
            model_completion is None
            or (not model_completion.get_message() and not model_completion.fn_calls)
        ) and retries > 0:
            model_completion = Model.chat(model_args)
            for fn_call in model_completion.get_or_stream_fn_calls():
                pass

            if not model_completion.get_message() and not model_completion.fn_calls:
                if temp_message_list is None:
                    message_list = message_manager.message_dicts
                    temp_message_list = message_list.copy()
                else:
                    temp_message_list = temp_message_list[:-1]
                temp_message_list.append({"role": "assistant", "content": ""})
                temp_message_list.append(
                    {
                        "role": "user",
                        "content": "You returned an empty response, which is disallowed. Please try again.",
                    }
                )
                node_system = message_manager.get_last_node_system_msg()
                if node_system is not None:
                    temp_message_list.append({"role": "system", "content": node_system})
                model_args.message_provider = temp_message_list

            retries -= 1

        if not model_completion.get_message() and not model_completion.fn_calls:
            raise ValueError("Failed to generate a non-empty user message")

        return model_completion


def turn_dump(turn):
    return {**turn.model_dump(), "class": turn.__class__.__name__}


def message_to_action(model_completion) -> Action:
    fn_calls = []
    for fn_call in model_completion.get_or_stream_fn_calls():
        fn_calls.append(fn_call)
    if fn_calls:
        return Action(
            name=fn_calls[0].name,
            kwargs=fn_calls[0].args,
            fn_calls=fn_calls,
        )
    else:
        return Action(
            name=RESPOND_ACTION_NAME,
            kwargs={"content": model_completion.get_or_stream_message()},
        )
