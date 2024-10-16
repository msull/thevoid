import os
import time
from base64 import b64encode

import streamlit as st
from logzero import logger
from simplesingletable import DynamoDbMemory
from supersullytools.llm.agent import AgentStates, ChatAgent
from supersullytools.llm.completions import CompletionHandler, ImagePromptMessage
from supersullytools.llm.trackers import (
    CompletionTracker,
    DailyUsageTracking,
    GlobalUsageTracker,
    SessionUsageTracking,
)
from supersullytools.streamlit.chat_agent_utils import ChatAgentUtils

st.set_page_config(initial_sidebar_state="collapsed")
hide_decoration_bar_style = """
    <style>
        header {visibility: hidden;}
    </style>
"""
st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)


@st.cache_resource
def get_memory() -> DynamoDbMemory:
    return DynamoDbMemory(logger=logger, table_name=os.environ.get("DYNAMODB_TABLE"))


@st.cache_resource
def get_completion_handler() -> CompletionHandler:
    memory = get_memory()
    trackers = get_trackers()
    completion_tracker = CompletionTracker(memory=memory, trackers=list(trackers))
    return CompletionHandler(
        logger=logger,
        debug_output_prompt_and_response=False,
        completion_tracker=completion_tracker,
    )


@st.cache_resource
def get_session_usage_tracker() -> SessionUsageTracking:
    return SessionUsageTracking()


def get_trackers() -> (
    tuple[GlobalUsageTracker, DailyUsageTracking, SessionUsageTracking]
):
    memory = get_memory()
    global_tracker = GlobalUsageTracker.ensure_exists(memory)
    todays_tracker = DailyUsageTracking.get_for_today(memory)
    return global_tracker, todays_tracker, get_session_usage_tracker()


@st.cache_resource
def get_agent() -> ChatAgent:
    # tool_profiles = {"all": [] + get_ddg_tools()}
    return ChatAgent(
        agent_description=(
            "You are playing the role of a magic mirror at a party; deliver a clever / witty response to the user "
            'as they chat with you. The "sessions" will always start with the famouse catch phrase. It is very important'
            "to keep your responses short, as they are being converted into sound via TTS and the experience is made "
            "worse if the responses are too long and take a while to beging playing. Similarly do not use markdown or "
            "fancy formatting in your responses, respond conversationally. Be playful, sassy, whip-smart!"
        ),
        logger=logger,
        completion_handler=get_completion_handler(),
        # tool_profiles=,
    )


def get_photo_description(image) -> str:
    msg = (
        "You are part of a magic mirror AI system at a party; a user has just stepped up to "
        'your physical device and pressed the button to initiate a new "session"; provide a brief '
        "description of the user in the attached photo which will be given to the magic mirror chatbot AI "
        "as it chats with the user in the role of a magic mirror. Do not try to read text on shirts or things like "
        "that, you are bad at it and it often steers the interaction into a poor conversation."
    )
    agent = get_agent()
    completion = agent.get_simple_completion(
        msg=ImagePromptMessage(
            content=msg,
            images=[b64encode(image.getvalue()).decode()],
            image_formats=["png"],
        ),
        # trying out Claude 3 Haiku, gpt-4o-mini
        model=agent.completion_handler.get_model_by_name_or_id("Claude 3 Haiku"),
    )
    return completion.content


def main():
    def _agent():
        agent = get_agent()
        return agent

    agent = _agent()
    agent_utils = ChatAgentUtils(agent)

    agent.completion_handler.completion_tracker.fixup_trackers()

    if "image_key" not in st.session_state:
        st.session_state.image_key = 1
        st.session_state.upload_images = []

    if "cam_input" not in st.session_state:
        st.session_state.cam_input = None

    if "image_description" not in st.session_state:
        st.session_state.image_description = None

    if st.session_state.cam_input:
        st.image(st.session_state.cam_input)
        st.write("#### ✨ Mirror, mirror on the wall, who's the fairest of them all? 🌟")
        if agent.working:
            with st.spinner("The mirror is thinking..."):
                while agent.working:
                    agent.run_agent()
                    time.sleep(0.05)

        def gch():
            return _agent().get_chat_history(True, False)

        if not gch():
            with st.spinner("Asking the mirror..."):
                image_description = get_photo_description(st.session_state.cam_input)
                st.session_state.image_description = image_description
                agent.force_add_chat_msg(
                    msg=(
                        "User description follows, respond as if the user had said to you "
                        '"Mirror mirror on the wall, who\'s the fairest of them all"\n\n'
                        f"<user_description>{image_description}</user_description>"
                    ),
                    role="system",
                )
                agent.current_state = AgentStates.received_message
                while agent.working:
                    agent.run_agent()
                    time.sleep(0.05)
                st.rerun()

        if chat_history := gch():

            def _reset():
                st.session_state.cam_input = None
                get_agent.clear()

            st.button(
                "Reset",
                on_click=_reset,
                use_container_width=True,
                help=st.session_state.image_description,
            )
            st.write(chat_history[-1].content)

            if chat_msg := st.chat_input("Talk to the mirror"):
                if agent_utils.add_user_message(
                    chat_msg, st.session_state.upload_images
                ):
                    if st.session_state.upload_images:
                        # clearing out the upload_images immediately causes weird IO errors, so
                        # just push to another key and overwrite it later
                        st.session_state.uploaded_images = (
                            st.session_state.upload_images
                        )
                        st.session_state.upload_images = []
                    time.sleep(0.01)
                    st.rerun()

    else:
        if not (cam_input := st.camera_input("cam", label_visibility="collapsed")):
            # st.header("Step up and let the mirror take a look")
            get_agent.clear()
            st.stop()
        st.session_state.cam_input = cam_input
        st.rerun()


if __name__ == "__main__":
    main()
