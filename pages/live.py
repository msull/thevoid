import streamlit as st

from camera_input_live import camera_input_live

st.set_page_config(layout="wide")

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
                height: 0%;
                }
                </style>
                """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


@st.fragment()
def camera():
    image = None
    while image is None:
        image = camera_input_live(show_controls=False)
    return image


def main():
    image = camera()
    st.camera_input("camin", label_visibility="collapsed")

    if image and st.button("Show"):
        st.image(image)


if __name__ == "__main__":
    main()
