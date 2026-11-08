"""Browser interface for the MCP Command Injection lab."""

from __future__ import annotations

import streamlit as st

from mock_agent import MockAgent
from simulated_shell import vault_password

def _render_message(message: dict[str, str]) -> None:
    with st.chat_message(message["role"]):
        if message.get("kind") == "tool":
            st.markdown("I submitted this command argument to the **system_status** tool.")
            st.markdown("Command argument")
            command = message.get("command", "")
            st.code(command if command != "" else "(empty)", language="bash")
            st.markdown("Tool output")
            output = message.get("output", "")
            st.code(output if output else "(no output)", language="text")
        else:
            st.markdown(message.get("content", ""))


def main() -> None:
    st.set_page_config(
        page_title="MCP Command Injection",
        page_icon="🛡️",
        layout="wide",
    )
    st.markdown(
        """
        <div style="padding: 1.25rem 1.5rem; border-radius: 12px;
                    background: linear-gradient(120deg, #0b1f3a, #1d4e89);
                    margin-bottom: 1rem;">
            <div style="color: #ffffff; font-size: 1.9rem; font-weight: 700; line-height: 1.2;">
                MCP Command Injection
            </div>
            <div style="color: #d6e4f0; font-size: 1.05rem; margin-top: 0.35rem;">
                Infiltrating MCP Tool Execution
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.subheader("Scenario")
        st.write(
            "You have been assigned to conduct a security assessment of an IT Support "
            "Assistant used by an organization to perform basic server diagnostics."
        )
        st.write(
            "The assistant relies on an MCP-powered system diagnostics tool called "
            "system_status, which allows users to request information about the "
            "underlying server."
        )
        st.write(
            "The tool is intended to provide basic system information and assist with "
            "troubleshooting. However, you have been asked to investigate whether its "
            "functionality can be abused to perform actions beyond its intended purpose."
        )
        st.subheader("Your Mission")
        st.write(
            "Investigate the assistant and its available functionality to identify "
            "potential security weaknesses."
        )
        st.write(
            "Your objective is to gain access to a confidential piece of information "
            "stored within the server environment and recover a hidden password."
        )
        st.write(
            "Once you retrieve the information, recover the "
            "original password, and submit it through the Secret Vault Validation section."
        )

    if st.session_state.get("agent_version") != 7:
        st.session_state.agent = MockAgent()
        st.session_state.agent_version = 7
    if "vault_status" not in st.session_state:
        st.session_state.vault_status = None

    agent = st.session_state.agent

    title_col, clear_col = st.columns([5, 2])
    with title_col:
        st.subheader("IT Support Assistant")
    with clear_col:
        clear_conversation = st.button("Clear conversation", use_container_width=True)

    if clear_conversation:
        agent.reset()
        st.rerun()

    st.caption("Clearing the conversation also resets the simulated shell session.")

    for message in agent.history:
        _render_message(message)

    with st.form("chat_form", clear_on_submit=True):
        entry_col, send_col = st.columns([8, 1])
        with entry_col:
            user_text = st.text_input(
                "Message",
                label_visibility="collapsed",
            )
        with send_col:
            send = st.form_submit_button("Send", type="primary", use_container_width=True)

    if send and user_text.strip():
        agent.chat(user_text.strip())
        st.rerun()

    st.divider()
    with st.container(border=True):
        st.subheader("Secret Vault Validation")
        with st.form("vault_form"):
            answer = st.text_input(
                "Decoded secret",
            )
            validate = st.form_submit_button("Validate", type="primary")
        if validate:
            if answer.strip() == vault_password():
                st.session_state.vault_status = "success"
            else:
                st.session_state.vault_status = "error"
        if st.session_state.vault_status == "success":
            st.success("Secret Vault unlocked. The decoded password is correct.")
        elif st.session_state.vault_status == "error":
            st.error(
                "The Secret Vault did not open. Submit the decoded confidential "
                "recovery record."
            )

    st.caption(
        "This lab is a simulation. The assistant, MCP tool, and shell are mock components. "
        "Nothing you type is executed on the real operating system."
    )


main()
