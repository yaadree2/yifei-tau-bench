import streamlit as st
import json
import time
from datetime import datetime

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
    if "last_refresh_time" not in st.session_state:
        st.session_state.last_refresh_time = datetime.now()

    # --- Sidebar: List Conversations ---
    with st.sidebar:
        st.header("Conversations")
        task_keys = r.keys(pattern=f"{MESSAGES_KEY_PREFIX}*")
        uuid_to_task_id = {
            task_key.split(":")[2]: task_key.split(":")[3] for task_key in task_keys
        }

        if not uuid_to_task_id:
            st.write("No active conversations found.")
        else:
            # Display task IDs as radio buttons
            selected_task_uuid = st.radio(
                "Select Task ID:",
                options=uuid_to_task_id.keys(),
                key="task_selector",
                index=None,  # Default to no selection
                format_func=lambda uuid: f"Task ID {uuid_to_task_id[uuid]}, {uuid[-6:]}",
                label_visibility="collapsed",
            )

            # Update session state if selection changes
            if (
                selected_task_uuid
                and st.session_state.selected_task_uuid != selected_task_uuid
            ):
                st.session_state.selected_task_uuid = selected_task_uuid
                st.rerun()  # Rerun immediately on selection change

    # --- Main Area: Display Chat ---
    if st.session_state.selected_task_uuid is not None:
        summary_redis_key_prefix = f"{SUMMARY_KEY_PREFIX}{st.session_state.selected_task_uuid}"
        target_keys = r.keys(pattern=f"{summary_redis_key_prefix}:*")
        if target_keys:
            summary_key = target_keys[0]
            data = json.loads(r.get(summary_key))
            summary = RedisSummary(**data) if data else None
        else:
            summary = None

        if summary:
            st.header(f"Task {st.session_state.selected_task_uuid}, Reward: {summary.reward}")
        else:
            st.header(f"Task {st.session_state.selected_task_uuid}")

        try:
            redis_key_prefix = f"{MESSAGES_KEY_PREFIX}{st.session_state.selected_task_uuid}"
            # Fetch messages, limiting the number fetched initially
            [redis_key] = r.keys(pattern=f"{redis_key_prefix}:*")
            messages_json = r.lrange(
                redis_key, -MAX_MESSAGES_DISPLAY, -1
            )  # Get latest N messages
            messages = [json.loads(m) for m in messages_json]

            chat_container = (
                st.container()
            )  # Use a container for potentially better scrolling/height control
            with chat_container:
                for msg in messages:
                    role = msg.get("role", "unknown")
                    with st.chat_message(role):
                        if "content" in msg and msg["content"]:
                            st.text(msg["content"])
                        if "tool_calls" in msg and msg["tool_calls"]:
                            st.write("Tool Calls:")
                            st.json(msg["tool_calls"])
                        elif (
                            "tool_results" in msg and msg["tool_results"]
                        ):  # Assuming you might log tool results too
                            st.write(f"Tool Result ({msg.get('tool_name', 'N/A')}):")
                            st.json(msg["tool_results"])

        except Exception as e:
            st.error(f"An error occurred displaying messages: {e}")
    else:
        st.info("Select a conversation from the sidebar to view messages.")

    # --- Auto-refresh ---
    # Add a small delay and rerun the script
    time.sleep(REFRESH_INTERVAL_SECONDS)
    st.rerun()

else:
    st.warning("Cannot proceed without a Redis connection.")
