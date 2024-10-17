import os
import time
from base64 import b64encode
from uuid import uuid4

import pandas as pd
import streamlit as st
from camera_input_live import camera_input_live
from logzero import logger
from simplesingletable import DynamoDbMemory
from supersullytools.llm.agent import AgentStates, ChatAgent
from supersullytools.llm.completions import CompletionHandler, ImagePromptMessage
from supersullytools.llm.trackers import (
    CompletionTracker,
    DailyUsageTracking,
    GlobalUsageTracker,
    SessionUsageTracking,
    UsageStats,
)
from gtts import gTTS
from io import BytesIO
from supersullytools.streamlit.chat_agent_utils import ChatAgentUtils, SlashCmd

st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
hide_streamlit_style = """
<style>
div[data-testid="stToolbar"] {
visibility: hidden;
height: 0%;
position: fixed;
}
div[data-testid="stDecoration"] {
visibility: hidden;
height: 0%;
position: fixed;
}
button[data-testid="stCameraInputButton"] {
visibility: hidden;
height: 0%;
position: fixed;
}
div[data-testid="stStatusWidget"] {
visibility: hidden;
height: 0%;
position: fixed;
}
#MainMenu {
visibility: hidden;
height: 0%;
}
header {
visibility: hidden;
height: 0%;
}
footer {
visibility: hidden;
height: 0%;s
}
</style>
""".strip()
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


@st.cache_resource
def get_memory() -> DynamoDbMemory:
    return DynamoDbMemory(logger=logger, table_name=os.environ.get("DYNAMODB_TABLE"))


# @st.cache_resource
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


def get_total_cost(tracker: "UsageStats"):
    stats_df = pd.DataFrame(
        {
            "count": tracker.completions_by_model,
            "input_tokens": tracker.input_tokens_by_model,
            "cached_input_tokens": tracker.cached_input_tokens_by_model,
            "output_tokens": tracker.output_tokens_by_model,
            "cost": tracker.compute_cost_per_model(),
        }
    )
    if not stats_df["count"].count():
        total_cost = 0.0
    else:
        total_cost = round(stats_df["cost"].sum(), 4)
    return float(total_cost)


def get_trackers() -> (
    tuple[GlobalUsageTracker, DailyUsageTracking, SessionUsageTracking]
):
    memory = get_memory()
    global_tracker = GlobalUsageTracker.ensure_exists(memory)
    todays_tracker = DailyUsageTracking.get_for_today(memory)
    if (total_cost := get_total_cost(todays_tracker)) > 0.1:
        todays_tracker.render_completion_cost_as_expander()
        logger.error(
            f"Cost has exceeded daily limit, halting session -- try again tomorrow! {total_cost=}"
        )
        st.error("Sorry, daily usage limit has been hit")
        st.stop()

    logger.debug(f"Total current cost {total_cost=}")
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
        "that, you are bad at it and it often steers the interaction into a poor conversation. Do make your description "
        "as detailed as possible, noting where possible the style of haircut, if they are stylish, etc. "
        "Any specific and notable details that can be used by the chatbot greatly enhance the user experience!"
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


@st.fragment()
def camera_display():
    st.camera_input("camin", label_visibility="collapsed")


@st.fragment()
def camera():
    return camera_input_live(show_controls=False)


def main():
    st.sidebar.subheader("Magic Mirror")

    def _agent():
        agent = get_agent()
        return agent

    agent = _agent()

    def _display_usage():
        for tracker in get_trackers():
            st.write(tracker.__class__.__name__)
            tracker.render_completion_cost_as_expander()

    agent_utils = ChatAgentUtils(
        agent,
        use_system_slash_cmds=False,
        extra_slash_cmds={
            "/usage": SlashCmd(
                name="Show Usage",
                mechanism=_display_usage,
                description="Display LLM Usage",
            )
        },
    )

    if "image_key" not in st.session_state:
        st.session_state.image_key = 1
        st.session_state.upload_images = []

    if "cam_input" not in st.session_state:
        st.session_state.cam_input = None

    if "image_description" not in st.session_state:
        st.session_state.image_description = None

    camera_display()

    if st.session_state.cam_input is None:
        image = camera()
    else:
        image = None

    if st.session_state.cam_input:
        st.sidebar.image(st.session_state.cam_input)
        st.sidebar.write(
            "#### ✨ Mirror, mirror on the wall, who's the fairest of them all? 🌟"
        )
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

            st.sidebar.caption(st.session_state.image_description)

            st.sidebar.button(
                "Reset",
                on_click=_reset,
                use_container_width=True,
            )

            st.sidebar.write(chat_history[-1].content)
            audio_file = get_audio(chat_history[-1].content)
            st.sidebar.audio(audio_file, autoplay=True)

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
        if st.button(
            "✨ Mirror, mirror on the wall, who's the fairest of them all? 🌟",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.cam_input = image
            st.rerun()


@st.cache_data
def get_audio(text: str):
    sound_file = BytesIO()
    # text = text.replace(", ", "")
    tts = gTTS(text, lang="en")
    tts.write_to_fp(sound_file)
    return sound_file


if __name__ == "__main__":
    main()
