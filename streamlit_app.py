import random
import re

import streamlit as st
import openai

SVG_R = r"(?:<\?xml\b[^>]*>[^<]*)?(?:<!--.*?-->[^<]*)*(?:<svg|<!DOCTYPE svg)\b"
SVG_RE = re.compile(SVG_R, re.DOTALL)

st.header("To the void...")
form = st.form("to the void", border=False)
user_input = form.text_area("input", height=200, label_visibility="collapsed")
if form.form_submit_button("cast your words"):
    if user_input.strip() != "":
        with st.spinner("into the void..."):
            response_type = random.choice(
                [
                    "A single word in ALL CAPS representing the mood.",
                    "A single word in ALL CAPS representing the mood.",
                    "A simple poem.",
                    "A simple haiku.",
                    'An SVG graphic (starting with <?xml version="1.0" encoding="UTF-8"?>\n<svg>, with some animation perhaps; do not include backticks or other markdown elements around the svg output).',
                    'An SVG graphic (starting with <?xml version="1.0" encoding="UTF-8"?>\n<svg>, with some animation perhaps; do not include backticks or other markdown elements around the svg output).',
                    'An SVG graphic (starting with <?xml version="1.0" encoding="UTF-8"?>\n<svg>, with some animation perhaps; do not include backticks or other markdown elements around the svg output).',
                    "ASCII art reflecting the emotion.",
                    # "A color or color palette (provide hex codes) symbolizing the mood.",
                    "A brief metaphorical statement capturing the essence of the feelings.",
                    "A brief metaphorical statement capturing the essence of the feelings.",
                    "A brief metaphorical statement capturing the essence of the feelings.",
                    "A brief story or anecdote mirroring the emotions.",
                    "A brief story or anecdote mirroring the emotions.",
                    "A sequence of emojis representing the user's feelings.",
                    "A sequence of emojis representing the user's feelings.",
                    # "An abstract mathematical expression related to the emotions.",
                    "A suggestion for a mindfulness or breathing exercise.",
                    "A completely freeform response of your choosing.",
                    "A completely freeform response of your choosing.",
                    "A completely freeform response of your choosing.",
                ]
            )
            prompt = f"""
            You are a compassionate and understanding listener. A user is venting their feelings:

            "{user_input}"

            Provide a CONCISE but empathetic and supportive response. Never offer advice or try to solve the problem.
            """.strip()

            # Call the OpenAI API
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                n=1,
                temperature=0.7,
            )

            empathic = response.choices[0].message.content.strip()
            st.header("From the void...")
            st.write(empathic)

            make_abstract = f"""
You are THE VOID. An Abstract Feelings AI.

A user is venting their feelings

<input>
{user_input}
</input>

And empathic response has been generated and displayed to the user already:

<empathic_response>
{empathic}
</empathic_response>

Generate a new, small, abstract response that carries a similar sentiment.

For this response, please generate a response of the following type:
{response_type}

Do not include any titles or headers. Output only the response.
""".strip()

            response2 = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": make_abstract}],
                max_completion_tokens=1000,
                n=1,
                temperature=1,
            )
            abstract = response2.choices[0].message.content.strip()

            st.divider()
            is_svg = SVG_RE.match(abstract) is not None
            if is_svg:
                st.image(abstract)
            else:
                st.write(abstract)
    else:
        st.write("Please enter some text before submitting.")
