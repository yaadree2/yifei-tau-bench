import streamlit as st
import json
import time
from datetime import datetime
from cashier.model.model_turn import AssistantTurn

from redis_util import MESSAGES_KEY_PREFIX, SUMMARY_KEY_PREFIX, RedisSummary, connect_to_redis

# --- Streamlit App Config (MUST be first Streamlit command) ---
st.set_page_config(layout="wide", page_title="Benchmark Visualizer")
# ---


REFRESH_INTERVAL_SECONDS = 2
MAX_MESSAGES_DISPLAY = (
    500  # Limit messages shown per conversation to avoid browser slowdown
)


# --- Redis Connection ---
@st.cache_resource
def get_redis_connection():
    return connect_to_redis(True)


r = get_redis_connection()

# --- Streamlit App ---
st.title("tau-bench Benchmark")

if r:
    # --- Session State Initialization ---
    if "selected_task_uuid" not in st.session_state:
        st.session_state.selected_task_uuid = None
    if "selected_task_id" not in st.session_state:
        st.session_state.selected_task_id = None

    # --- Sidebar: List Conversations ---
    with st.sidebar:
        st.header("Conversations")

        @st.experimental_fragment(run_every=REFRESH_INTERVAL_SECONDS)
        def display_sidebar():
            task_keys = r.keys(pattern=f"{MESSAGES_KEY_PREFIX}*")
            uuid_to_task_id = {
                task_key.split(":")[2]: task_key.split(":")[3] for task_key in task_keys
            }

            summary_keys = r.keys(pattern=f"{SUMMARY_KEY_PREFIX}*")
            summary_values = r.mget(summary_keys)
            summary_key_to_value = {
                key.split(":")[2]: RedisSummary(**json.loads(value)) if value else None
                for key, value in zip(summary_keys, summary_values)
            }

            def format_func(uuid):
                summary_value = summary_key_to_value.get(uuid, None)
                if summary_value:
                    return f"Task ID {uuid_to_task_id[uuid]}, {uuid[-6:]}, reward: {summary_value.reward}"
                else:
                    return f"Task ID {uuid_to_task_id[uuid]}, {uuid[-6:]}"


            if not uuid_to_task_id:
                st.write("No active conversations found.")
            else:
                # Display task IDs as radio buttons
                selected_task_uuid = st.radio(
                    "Select Task ID:",
                    options=uuid_to_task_id.keys(),
                    key="task_selector",
                    index=None,  # Default to no selection
                    format_func=format_func,
                    label_visibility="collapsed",
                )

                # Update session state if selection changes
                if (
                    selected_task_uuid
                    and st.session_state.selected_task_uuid != selected_task_uuid
                ):
                    st.session_state.selected_task_uuid = selected_task_uuid
                    st.session_state.selected_task_id = uuid_to_task_id[selected_task_uuid]
                    st.session_state.last_task_switch_time = time.time()
                    st.rerun()  # Rerun immediately on selection change

        display_sidebar()

    # --- Main Area: Display Chat ---
    if st.session_state.selected_task_uuid is not None:
        summary_redis_key = f"{SUMMARY_KEY_PREFIX}{st.session_state.selected_task_uuid}"
        json_data = r.get(summary_redis_key)
        if json_data:
            data = json.loads(r.get(summary_redis_key))
            summary = RedisSummary(**data)
        else:
            summary = None

        if summary:
            st.header(f"Task {st.session_state.selected_task_uuid}, Reward: {summary.reward}")
        else:
            st.header(f"Task {st.session_state.selected_task_uuid}")

        # Define the fragment that will auto-refresh
        @st.experimental_fragment(run_every=REFRESH_INTERVAL_SECONDS)
        def display_chat_messages():
            try:
                current_uuid = st.session_state.selected_task_uuid
                current_task_id = st.session_state.selected_task_id
                if not current_uuid or not current_task_id: # Avoid error if state cleared during refresh
                    return

                messages_json = r.lrange(
                    f"{MESSAGES_KEY_PREFIX}{current_uuid}:{current_task_id}", -MAX_MESSAGES_DISPLAY, -1
                )  # Get latest N messages
                messages = [json.loads(m) for m in messages_json]

                # Use a key based on the conversation ID to ensure the container itself is unique per conversation
                container_key = f"chat_display_container_{current_uuid}"
                with st.container(key=container_key):
                    for msg in messages:
                        role = msg.get("role", 'assistant')
                        with st.chat_message(role):
                            if role == 'user':
                                st.text(msg["content"])
                            else:
                                if msg['msg_content'] and not msg['fn_call_to_fn_output']:
                                    st.text(msg['msg_content'])
                                else:
                                    st.write("**Tool Calls**")
                                    for fn_call_dict in msg['fn_call_to_fn_output']:
                                        new_dict = fn_call_dict['function_call'].copy()
                                        new_dict.pop('input_args_json')
                                        new_dict.pop('source_provider')
                                        new_dict['output'] = fn_call_dict['value']
                                        st.json(new_dict)
                                        st.divider()
            except Exception as e:
                # Check if the error is due to accessing state during a switch/refresh edge case
                if 'selected_task_uuid' in str(e) or 'selected_task_id' in str(e):
                    pass # Ignore errors likely caused by state being None temporarily
                else:
                    st.error(f"An error occurred displaying messages: {e}")

        # Call the fragment function to display the chat
        display_chat_messages()

    else:
        st.info("Select a conversation from the sidebar to view messages.")

else:
    st.warning("Cannot proceed without a Redis connection.")
