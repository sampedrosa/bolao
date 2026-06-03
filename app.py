from __future__ import annotations

import base64
import json
import os
import re
import unicodedata
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from PIL import Image


ROOT = Path(__file__).parent
FLAGS_DIR = ROOT / "bandeiras"
REGRAS_PATH = ROOT / "regras.md"
TZ = ZoneInfo("America/Sao_Paulo")

JOGOS_COLUMNS = ["Id", "Data", "Fase", "Time1", "Time2", "Gols1", "Gols2", "Resultado"]
SELECOES_COLUMNS = ["Nome", "Grupo", "Bandeira"]
JOGADORES_COLUMNS = ["Nome", "Posição", "GC1", "GC4", "GC6", "GD", "GO", "GQ", "GS", "GF"]

GROUP_DEADLINE = datetime(2026, 6, 11, 16, 0, tzinfo=TZ)
FINALISTAS_START = datetime(2026, 6, 24, 1, 0, tzinfo=TZ)
FINALISTAS_END = datetime(2026, 6, 28, 16, 0, tzinfo=TZ)
ELIMINATORIAS_START = datetime(2026, 6, 24, 1, 0, tzinfo=TZ)
ELIMINATORIAS_END = datetime(2026, 7, 18, 18, 0, tzinfo=TZ)

VALID_RESULTS = {"1", "2", "E"}


st.set_page_config(
    page_title="Bolão Copa 2026",
    page_icon="⚽",
    layout="centered",
    initial_sidebar_state="expanded",
)


def apply_styles(show_sidebar: bool) -> None:
    sidebar_css = (
        """
        section[data-testid="stSidebar"] {
            width: min(calc(440px + 6ch), 92vw) !important;
        }

        section[data-testid="stSidebar"] > div {
            width: min(calc(440px + 6ch), 92vw) !important;
        }

        @media (max-width: 760px) {
            section[data-testid="stSidebar"],
            button[kind="headerNoPadding"],
            [data-testid="collapsedControl"] {
                display: none !important;
            }
        }
        """
        if show_sidebar
        else """
        section[data-testid="stSidebar"],
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        """
    )

    st.markdown(
        """
        <style>
        """
        + sidebar_css
        + """
        :root,
        html,
        body,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"] {
            color-scheme: light !important;
            background: #f8f6ef !important;
            color: #152033 !important;
        }

        [data-testid="stSidebar"],
        [data-testid="stSidebar"] > div {
            color-scheme: light !important;
            background: #ffffff !important;
            color: #152033 !important;
        }

        .main .block-container {
            max-width: 920px;
            padding-top: 1.1rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3 {
            letter-spacing: 0;
        }

        .st-key-login_shell {
            max-width: 780px;
            margin: 2.75rem auto 0 auto;
        }

        .login-title {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1.05rem;
            text-align: center;
            font-size: clamp(2.35rem, 5vw, 3.25rem);
            line-height: 1.05;
            font-weight: 820;
            color: #0d1320;
            margin: 0.2rem 0 3.2rem 0;
        }

        .login-title img {
            width: auto;
            height: clamp(5.8rem, 9.4vw, 8rem);
            object-fit: contain;
            flex: 0 0 auto;
            filter: drop-shadow(0 10px 14px rgba(96, 62, 18, 0.18));
        }

        .login-heading {
            font-size: clamp(2rem, 4.6vw, 2.65rem);
            line-height: 1.1;
            font-weight: 800;
            color: #0d1320;
            margin: 0 0 1.15rem 0.15rem;
        }

        .st-key-login_select div[data-baseweb="select"] > div {
            min-height: 4.35rem;
            border-radius: 10px;
            border-color: #d1b064;
            background: #fffdf7;
            box-shadow: 0 8px 18px rgba(41, 28, 9, 0.05);
            display: flex;
            align-items: center;
        }

        .st-key-login_select div[data-baseweb="select"] {
            font-size: 1.28rem;
        }

        .st-key-login_select div[data-baseweb="select"] div,
        .st-key-login_select div[data-baseweb="select"] span,
        .st-key-login_select div[data-baseweb="select"] input {
            font-size: 1.28rem;
            line-height: 1.2;
            color: #0d1320;
        }

        .st-key-login_select div[data-baseweb="select"] input {
            display: block !important;
            height: auto !important;
            min-height: 0 !important;
            padding: 0 !important;
            caret-color: #0d1320;
        }

        .st-key-login_select div[data-baseweb="select"] svg {
            color: #5c4a23;
        }

        div[role="option"] {
            font-size: 1.22rem !important;
        }

        .st-key-login_enter_btn button,
        .st-key-login_register_btn button,
        .st-key-login_dashboard button {
            min-height: 4.35rem;
            border-radius: 10px;
            font-size: 1.32rem;
            font-weight: 800;
            border-color: #d1b064;
            box-shadow: 0 8px 18px rgba(41, 28, 9, 0.05);
        }

        .st-key-login_enter_btn button {
            background: #1f7a4d;
            border-color: #1f7a4d;
            color: #ffffff;
        }

        .st-key-login_enter_btn button:hover:enabled {
            background: #17653f;
            border-color: #17653f;
        }

        .st-key-login_enter_btn button:disabled {
            background: #fffdf7;
            border-color: #d8ccb1;
            color: #9a8d74;
            opacity: 1;
        }

        .st-key-login_register_btn button,
        .st-key-login_dashboard button {
            margin-top: 0.75rem;
        }

        .st-key-login_register_btn button {
            background: #0d1320;
            border-color: #0d1320;
            color: #f8f6ef;
        }

        .st-key-login_register_btn button:hover:enabled {
            background: #1a2333;
            border-color: #1a2333;
            color: #ffffff;
        }

        .st-key-login_dashboard button {
            background: #fff7df;
            color: #8a6a19;
        }

        .st-key-login_dashboard button:disabled {
            background: #f0eadc;
            border-color: #d8ccb1;
            color: #a58b51;
        }

        .login-help {
            color: #5c4a23;
            font-size: 1.04rem;
            margin: -0.25rem 0 0.9rem 0.15rem;
        }

        .st-key-principal_shell {
            max-width: 780px;
            margin: 2.15rem auto 0 auto;
        }

        .principal-eyebrow {
            color: #8a6a19;
            font-size: 0.92rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
        }

        .principal-title {
            color: #0d1320;
            font-size: clamp(2.25rem, 5vw, 3.15rem);
            line-height: 1.05;
            font-weight: 850;
            margin: 0;
        }

        .principal-subtitle {
            color: #5c4a23;
            font-size: 1.04rem;
            margin: 0.85rem 0 1.65rem 0;
        }

        .top-user {
            border: 1px solid #d1b064;
            border-radius: 14px;
            padding: 1.1rem 1.15rem;
            margin: 0 0 1.35rem 0;
            background: #fffdf7;
            box-shadow: 0 10px 24px rgba(41, 28, 9, 0.06);
        }

        .top-user-label {
            color: #8a6a19;
            font-size: 0.85rem;
            font-weight: 800;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }

        .user-name {
            font-size: clamp(1.45rem, 4vw, 2rem);
            line-height: 1.1;
            font-weight: 850;
            color: #0d1320;
            margin-top: 0.25rem;
        }

        .action-note {
            color: #6f5f3d;
            font-size: 0.92rem;
            margin: -0.2rem 0 1rem 0;
        }

        .st-key-action_groups button,
        .st-key-action_finalistas button,
        .st-key-action_eliminatorias button,
        .st-key-principal_dashboard button {
            min-height: 4.65rem;
            border-radius: 12px;
            font-size: 1.34rem;
            line-height: 1.2;
            font-weight: 850;
            border-color: #d1b064;
            box-shadow: 0 10px 24px rgba(41, 28, 9, 0.06);
            margin-bottom: 0.75rem;
        }

        .st-key-action_groups button,
        .st-key-action_finalistas button,
        .st-key-action_eliminatorias button {
            background: #fffdf7;
            color: #0d1320;
        }

        .st-key-action_groups button:hover:enabled,
        .st-key-action_finalistas button:hover:enabled,
        .st-key-action_eliminatorias button:hover:enabled {
            border-color: #1f7a4d;
            color: #17653f;
            background: #ffffff;
        }

        .st-key-action_groups button:disabled,
        .st-key-action_finalistas button:disabled,
        .st-key-action_eliminatorias button:disabled {
            background: #ece4d5;
            border-color: #d8ccb1;
            color: #8b8270;
            opacity: 1;
        }

        .st-key-principal_dashboard button {
            background: #fff7df;
            color: #8a6a19;
        }

        .st-key-principal_dashboard button:disabled {
            background: #f0eadc;
            border-color: #d8ccb1;
            color: #a58b51;
        }

        .st-key-groups_shell {
            max-width: 760px;
            margin: 4.75rem auto 0 auto;
        }

        .groups-eyebrow {
            color: #8a6a19;
            font-size: 0.92rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
        }

        .groups-title {
            color: #0d1320;
            font-size: clamp(2.2rem, 5vw, 3.05rem);
            line-height: 1.05;
            font-weight: 850;
            margin: 0;
        }

        .groups-participant {
            color: #5c4a23;
            font-size: 1.03rem;
            margin: 0.8rem 0 1.25rem 0;
        }

        .groups-participant strong {
            color: #0d1320;
            font-weight: 850;
        }

        .groups-list-start {
            height: 0.3rem;
        }

        .match-meta {
            color: #8a6a19;
            font-size: 0.95rem;
            font-weight: 700;
            margin-bottom: 0.7rem;
        }

        .team-name {
            font-weight: 850;
            color: #0d1320;
            line-height: 1.2;
            overflow-wrap: anywhere;
        }

        .team-name.right {
            text-align: right;
        }

        .score-sep {
            text-align: center;
            font-size: 1.3rem;
            font-weight: 800;
            color: #526070;
            padding-top: 2.15rem;
        }

        .match-versus {
            text-align: center;
            font-size: 1.25rem;
            font-weight: 800;
            color: #8a6a19;
            padding-top: 0.35rem;
        }

        .st-key-group_actions_bar {
            position: fixed !important;
            top: 4.25rem !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            width: min(920px, calc(100vw - 2rem)) !important;
            z-index: 100000 !important;
            background: #fffdf7 !important;
            border: 1px solid #d1b064;
            border-radius: 12px;
            padding: 0.55rem 0.75rem 0.7rem 0.75rem;
            margin: 0;
            box-shadow: 0 10px 24px rgba(41, 28, 9, 0.10);
        }

        .st-key-group_actions_bar button {
            min-height: 3.15rem;
            border-radius: 9px;
            font-size: 1.05rem;
            font-weight: 850;
        }

        .st-key-group_actions_bar > div[data-testid="stLayoutWrapper"] > div[data-testid="stHorizontalBlock"] button[data-testid="stBaseButton-primary"],
        .st-key-group_actions_bar > div[data-testid="stLayoutWrapper"] > div[data-testid="stHorizontalBlock"] button[data-testid="stBaseButton-primaryFormSubmit"] {
            background: #1f7a4d !important;
            border-color: #1f7a4d !important;
            color: #ffffff !important;
        }

        .st-key-group_actions_bar > div[data-testid="stLayoutWrapper"] > div[data-testid="stHorizontalBlock"] button[data-testid="stBaseButton-primary"]:hover:enabled,
        .st-key-group_actions_bar > div[data-testid="stLayoutWrapper"] > div[data-testid="stHorizontalBlock"] button[data-testid="stBaseButton-primaryFormSubmit"]:hover:enabled {
            background: #17653f !important;
            border-color: #17653f !important;
            color: #ffffff !important;
        }

        .st-key-group_actions_bar > div[data-testid="stLayoutWrapper"] > div[data-testid="stHorizontalBlock"] button[data-testid="stBaseButton-secondary"],
        .st-key-group_actions_bar > div[data-testid="stLayoutWrapper"] > div[data-testid="stHorizontalBlock"] button[data-testid="stBaseButton-secondaryFormSubmit"] {
            background: #fffdf7 !important;
            border-color: #d1b064 !important;
            color: #0d1320 !important;
        }

        .st-key-group_actions_bar > div[data-testid="stLayoutWrapper"] > div[data-testid="stHorizontalBlock"] button[data-testid="stBaseButton-secondary"]:hover:enabled,
        .st-key-group_actions_bar > div[data-testid="stLayoutWrapper"] > div[data-testid="stHorizontalBlock"] button[data-testid="stBaseButton-secondaryFormSubmit"]:hover:enabled {
            background: #ffffff !important;
            border-color: #1f7a4d !important;
            color: #17653f !important;
        }

        div[class*="st-key-group_"][class*="_gols"] {
            min-height: 3.15rem;
            overflow: visible !important;
        }

        div[class*="st-key-group_"][class*="_gols"] > div,
        div[class*="st-key-group_"][class*="_gols"] [data-baseweb="input"],
        div[class*="st-key-group_"][class*="_gols"] [data-testid="stTextInputRootElement"] {
            min-height: 2.55rem;
            overflow: visible !important;
        }

        div[class*="st-key-group_"][class*="_gols"] input {
            text-align: center;
            height: 2.55rem;
            min-height: 2.55rem;
            padding-left: 0.25rem;
            padding-right: 0.25rem;
            border-radius: 10px;
            border: 1px solid #d1b064;
            background: #fffdf7;
            color: #0d1320;
            font-size: 1.05rem;
            font-weight: 850;
        }

        div[class*="st-key-group_"][class*="_jogador"] div[data-baseweb="select"] > div {
            min-height: 2.8rem;
            border-radius: 10px;
            border-color: #d1b064;
            background: #fffdf7;
            color: #0d1320;
        }

        div[class*="st-key-group_"][class*="_jogador"] div[data-baseweb="select"] * {
            font-weight: 700;
        }

        .st-key-groups_shell div[data-testid="stExpander"] {
            border: 1px solid #d1b064;
            border-radius: 12px;
            background: #fffdf7;
            box-shadow: 0 8px 20px rgba(41, 28, 9, 0.05);
            margin-bottom: 0.85rem;
            overflow: hidden;
        }

        .st-key-groups_shell div[data-testid="stExpander"] details summary {
            min-height: 3.7rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .st-key-groups_shell div[data-testid="stExpander"] details summary p {
            color: #0d1320 !important;
            font-size: 1.28rem !important;
            font-weight: 850 !important;
        }

        .st-key-groups_shell [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: #d8ccb1 !important;
            border-radius: 12px !important;
            background: #fffdf7 !important;
            box-shadow: 0 8px 18px rgba(41, 28, 9, 0.04);
            padding-bottom: 0.75rem !important;
        }

        @media (max-width: 640px) {
            .main .block-container {
                padding-left: 0.85rem;
                padding-right: 0.85rem;
            }

            .user-name {
                font-size: 1.15rem;
            }

            .team-name {
                font-size: 0.74rem;
            }

            .st-key-login_shell {
                margin-top: 1.2rem;
            }

            .login-title {
                gap: 0.7rem;
                font-size: 2.08rem;
                margin-bottom: 2.15rem;
            }

            .login-title img {
                height: 4.65rem;
            }

            .login-heading {
                margin-bottom: 0.8rem;
            }

            .st-key-login_select div[data-baseweb="select"] > div,
            .st-key-login_enter_btn button,
            .st-key-login_register_btn button,
            .st-key-login_dashboard button {
                min-height: 3.65rem;
            }

            .st-key-login_enter_btn button,
            .st-key-login_register_btn button,
            .st-key-login_dashboard button {
                font-size: 1.18rem;
            }

            .st-key-principal_shell {
                margin-top: 1.15rem;
            }

            .principal-subtitle {
                margin-bottom: 1.15rem;
            }

            .top-user {
                padding: 0.95rem 1rem;
            }

            .user-name {
                font-size: 1.55rem;
            }

            .st-key-action_groups button,
            .st-key-action_finalistas button,
            .st-key-action_eliminatorias button,
            .st-key-principal_dashboard button {
                min-height: 4.15rem;
                font-size: 1.14rem;
            }

            .st-key-groups_shell {
                margin-top: 4.6rem;
            }

            .groups-participant {
                margin-bottom: 0.85rem;
            }

            .st-key-group_actions_bar {
                top: 3.75rem !important;
                width: calc(100vw - 1rem) !important;
                padding: 0.45rem 0.5rem 0.55rem 0.5rem;
            }

            .st-key-group_actions_bar button {
                min-height: 2.85rem;
                font-size: 0.98rem;
            }

            .st-key-groups_shell div[data-testid="stExpander"] details summary {
                min-height: 3.25rem;
            }

            .st-key-groups_shell div[data-testid="stExpander"] details summary p {
                font-size: 1.13rem !important;
            }

            div[class*="st-key-group_"][class*="_gols"] input {
                height: 2.35rem;
                min-height: 2.35rem;
                font-size: 0.95rem;
            }

            div[class*="st-key-group_"][class*="_gols"] {
                min-height: 2.85rem;
            }

            .st-key-groups_shell div[data-testid="stHorizontalBlock"] {
                display: flex !important;
                flex-direction: row !important;
                flex-wrap: nowrap !important;
                align-items: center !important;
                gap: 0.32rem !important;
            }

            .st-key-groups_shell div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
                min-width: 0 !important;
                width: auto !important;
            }

            .st-key-groups_shell div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(1),
            .st-key-groups_shell div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(7) {
                flex: 0 0 26px !important;
            }

            .st-key-groups_shell div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(2),
            .st-key-groups_shell div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(6) {
                flex: 1 1 0 !important;
            }

            .st-key-groups_shell div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(3),
            .st-key-groups_shell div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(5) {
                flex: 0 0 38px !important;
            }

            .st-key-groups_shell div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(4) {
                flex: 0 0 14px !important;
            }

            .st-key-groups_shell div[data-testid="stImage"] img {
                width: 24px !important;
                max-width: 24px !important;
            }

            .match-versus {
                font-size: 1rem;
                padding-top: 0;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def rerun() -> None:
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


def read_regras() -> str:
    return REGRAS_PATH.read_text(encoding="utf-8")


def get_secret_value(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value

    try:
        for name in names:
            if name in st.secrets and st.secrets[name]:
                return str(st.secrets[name])

        if "supabase" in st.secrets:
            supabase_secrets = st.secrets["supabase"]
            for name in names:
                key = name.removeprefix("SUPABASE_").lower()
                if key in supabase_secrets and supabase_secrets[key]:
                    return str(supabase_secrets[key])
    except (FileNotFoundError, KeyError, AttributeError):
        return None

    return None


@st.cache_resource(show_spinner=False)
def get_supabase_client() -> Any:
    url = get_secret_value("SUPABASE_URL")
    key = get_secret_value("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_KEY")
    if not url or not key:
        st.error(
            "Configure SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY nos Secrets do Streamlit."
        )
        st.stop()

    try:
        from supabase import create_client
    except ImportError as exc:
        st.error("Instale a dependência 'supabase' ou rode 'pip install -r requirements.txt'.")
        raise exc

    return create_client(url, key)


def supabase_select(table: str, order_by: str | None = None) -> list[dict[str, Any]]:
    client = get_supabase_client()
    query = client.table(table).select("*")
    if order_by:
        query = query.order(order_by)
    response = query.execute()
    return response.data or []


def dataframe_from_records(
    records: list[dict[str, Any]],
    columns: list[str],
) -> pd.DataFrame:
    df = pd.DataFrame.from_records(records)
    for column in columns:
        if column not in df.columns:
            df[column] = ""
    return df[columns].fillna("").astype(str)


def load_jogos() -> pd.DataFrame:
    df = dataframe_from_records(supabase_select("jogos"), JOGOS_COLUMNS)
    df["_data"] = pd.to_datetime(df["Data"])
    return df.sort_values("_data").reset_index(drop=True)


def load_selecoes() -> pd.DataFrame:
    return dataframe_from_records(
        supabase_select("selecoes", order_by="Nome"),
        SELECOES_COLUMNS,
    )


def load_jogadores() -> pd.DataFrame:
    return dataframe_from_records(
        supabase_select("jogadores", order_by="Nome"),
        JOGADORES_COLUMNS,
    )


def decode_json_field(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        return json.loads(value)
    return {}


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(read_regras())


def image_data_uri(path: Path, crop_alpha: bool = False) -> str:
    if not path.exists():
        return ""

    if crop_alpha:
        image = Image.open(path).convert("RGBA")
        bbox = image.getbbox()
        if bbox:
            image = image.crop(bbox)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"

    mime_type = "image/webp" if path.suffix.lower() == ".webp" else "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def empty_palpite(jogo_id: str) -> dict[str, Any]:
    return {
        "jogo": jogo_id,
        "gols1": None,
        "gols2": None,
        "resultado": None,
        "jogador": None,
    }


def jogo_ids() -> list[str]:
    return load_jogos()["Id"].tolist()


def normalize_participant(participant: dict[str, Any]) -> dict[str, Any]:
    participant.setdefault("nome", "")
    participant.setdefault("pontos", 0)
    finalistas = participant.get("finalistas") or {}
    participant["finalistas"] = {str(i): finalistas.get(str(i)) for i in range(1, 5)}

    guesses_by_id = {
        str(guess.get("jogo")): guess
        for guess in participant.get("palpites", [])
        if guess.get("jogo") is not None
    }
    normalized_guesses = []
    for game_id in jogo_ids():
        guess = empty_palpite(game_id)
        guess.update(guesses_by_id.get(game_id, {}))
        guess["jogo"] = game_id
        normalized_guesses.append(guess)
    participant["palpites"] = normalized_guesses
    return participant


def load_participantes() -> dict[str, Any]:
    rows = supabase_select("participantes_atuais", order_by="nome")
    participantes = []
    for row in rows:
        participant = decode_json_field(row.get("dados"))
        if not participant.get("nome"):
            participant["nome"] = row.get("nome", "")
        participantes.append(normalize_participant(participant))
    return {"participantes": participantes}


def save_participantes(
    data: dict[str, Any],
    only_names: list[str] | None = None,
) -> None:
    data["participantes"] = [
        normalize_participant(participant) for participant in data.get("participantes", [])
    ]

    client = get_supabase_client()
    selected_names = (
        {normalize_name(name) for name in only_names}
        if only_names is not None
        else None
    )
    for participant in data["participantes"]:
        name = participant.get("nome", "")
        normalized_name = normalize_name(name)
        if not normalized_name:
            continue
        if selected_names is not None and normalized_name not in selected_names:
            continue

        client.table("participantes").upsert(
            {
                "nome_normalizado": normalized_name,
                "nome": name,
            },
            on_conflict="nome_normalizado",
        ).execute()
        client.table("participantes_versoes").insert(
            {
                "nome_normalizado": normalized_name,
                "nome": name,
                "dados": participant,
            }
        ).execute()


def normalize_name(value: str) -> str:
    stripped = " ".join(value.strip().split())
    no_accents = "".join(
        char
        for char in unicodedata.normalize("NFKD", stripped)
        if not unicodedata.combining(char)
    )
    return no_accents.casefold()


def validate_new_name(raw_name: str, existing_names: list[str]) -> tuple[bool, str, str]:
    name = " ".join(raw_name.strip().split())
    if not name:
        return False, name, "Digite um nome."
    if len(name) > 20:
        return False, name, "O nome deve ter no máximo 20 caracteres."
    if not re.search(r"[A-Za-zÀ-ÿ0-9]", name):
        return False, name, "Use pelo menos uma letra ou número."

    normalized = normalize_name(name)
    existing = {normalize_name(existing_name) for existing_name in existing_names}
    if normalized in existing:
        return False, name, "Esse nome já está cadastrado."

    return True, name, ""


def current_participant(data: dict[str, Any]) -> dict[str, Any] | None:
    logged_name = st.session_state.get("participant_name")
    for participant in data.get("participantes", []):
        if participant.get("nome") == logged_name:
            return participant
    return None


def get_guess_map(participant: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {guess["jogo"]: guess for guess in participant.get("palpites", [])}


def is_brazil_game(game: pd.Series) -> bool:
    return game["Time1"] == "Brasil" or game["Time2"] == "Brasil"


def is_filled(value: Any) -> bool:
    return value is not None and value != ""


def is_group_complete(participant: dict[str, Any]) -> bool:
    guesses = get_guess_map(participant)
    group_games = load_jogos().query("Fase == 'Grupo'")
    for _, game in group_games.iterrows():
        guess = guesses.get(game["Id"], {})
        has_score = is_filled(guess.get("gols1")) and is_filled(guess.get("gols2"))
        has_result = guess.get("resultado") in VALID_RESULTS
        has_player = (not is_brazil_game(game)) or is_filled(guess.get("jogador"))
        if not (has_score and has_result and has_player):
            return False
    return True


def is_finalistas_complete(participant: dict[str, Any]) -> bool:
    finalistas = participant.get("finalistas", {})
    return all(is_filled(finalistas.get(str(i))) for i in range(1, 5))


def is_eliminatorias_complete(participant: dict[str, Any]) -> bool:
    guesses = get_guess_map(participant)
    knockout_games = load_jogos().query("Fase != 'Grupo'")
    for _, game in knockout_games.iterrows():
        guess = guesses.get(game["Id"], {})
        has_score = is_filled(guess.get("gols1")) and is_filled(guess.get("gols2"))
        has_result = guess.get("resultado") in VALID_RESULTS
        if not (has_score and has_result):
            return False
    return True


def get_header(name: str) -> str:
    headers = getattr(st.context, "headers", {}) or {}
    for key in (name, name.lower(), name.title()):
        try:
            value = headers.get(key)
        except AttributeError:
            value = None
        if value:
            return str(value)
    return ""


def is_mobile_client() -> bool:
    try:
        forced_mobile = st.query_params.get("mobile")
    except Exception:
        forced_mobile = None
    if str(forced_mobile).lower() in {"1", "true", "sim", "yes"}:
        return True

    user_agent = get_header("user-agent").lower()
    mobile_markers = (
        "android",
        "iphone",
        "ipad",
        "ipod",
        "mobile",
        "windows phone",
        "opera mini",
    )
    return any(marker in user_agent for marker in mobile_markers)


def go_to(page: str) -> None:
    st.session_state["page"] = page
    st.session_state["confirm_group_back"] = False
    rerun()


def login_as(name: str, show_mobile_rules: bool = False) -> None:
    st.session_state["participant_name"] = name
    st.session_state["page"] = "principal"
    st.session_state["group_draft_owner"] = None
    st.session_state["mobile_rules_pending"] = show_mobile_rules
    rerun()


def format_datetime(value: str) -> str:
    dt = datetime.fromisoformat(value)
    return dt.strftime("%d/%m/%Y às %H:%M")


def result_from_score(gols1: int | None, gols2: int | None) -> str | None:
    if gols1 is None or gols2 is None:
        return None
    if gols1 > gols2:
        return "1"
    if gols2 > gols1:
        return "2"
    return "E"


def parse_goal(raw: Any) -> tuple[int | None, str | None]:
    value = "" if raw is None else str(raw).strip()
    if value == "":
        return None, None
    if not value.isdigit():
        return None, "Use apenas números inteiros de 0 a 99."
    number = int(value)
    if number < 0 or number > 99:
        return None, "Use valores de 0 a 99."
    return number, None


def flag_path(team_name: str) -> Path | None:
    selecoes = load_selecoes()
    match = selecoes.loc[selecoes["Nome"] == team_name]
    if match.empty:
        return None

    path = FLAGS_DIR / match.iloc[0]["Bandeira"]
    return path if path.exists() else None


def render_team(team_name: str) -> None:
    cols = st.columns([0.24, 0.76])
    path = flag_path(team_name)
    with cols[0]:
        if path:
            st.image(str(path), width=38)
    with cols[1]:
        st.markdown(f'<div class="team-name">{team_name}</div>', unsafe_allow_html=True)


def render_flag(team_name: str, width: int = 34) -> None:
    path = flag_path(team_name)
    if path:
        st.image(str(path), width=width)


def render_match_score_line(game: pd.Series) -> None:
    cols = st.columns([0.13, 0.28, 0.12, 0.05, 0.12, 0.28, 0.13], gap="small")
    with cols[0]:
        render_flag(game["Time1"])
    with cols[1]:
        st.markdown(f'<div class="team-name">{game["Time1"]}</div>', unsafe_allow_html=True)
    with cols[2]:
        st.text_input(
            f"Gols de {game['Time1']}",
            key=f"group_{game['Id']}_gols1",
            max_chars=2,
            label_visibility="collapsed",
        )
    with cols[3]:
        st.markdown('<div class="match-versus">x</div>', unsafe_allow_html=True)
    with cols[4]:
        st.text_input(
            f"Gols de {game['Time2']}",
            key=f"group_{game['Id']}_gols2",
            max_chars=2,
            label_visibility="collapsed",
        )
    with cols[5]:
        st.markdown(
            f'<div class="team-name right">{game["Time2"]}</div>',
            unsafe_allow_html=True,
        )
    with cols[6]:
        render_flag(game["Time2"])


def participant_names(data: dict[str, Any]) -> list[str]:
    return [participant.get("nome", "") for participant in data.get("participantes", [])]


def dashboard_available() -> bool:
    return datetime.now(TZ) >= GROUP_DEADLINE


def render_dashboard_button(key: str) -> None:
    available = dashboard_available()
    if st.button(
        "Visualizar Jogos e Ranking",
        key=key,
        use_container_width=True,
        disabled=not available,
    ):
        go_to("dashboard")
    if not available:
        st.caption("Disponível a partir de 11/06/2026 às 16:00.")


def register_dialog(data: dict[str, Any], names: list[str]) -> None:
    @st.dialog("Cadastrar")
    def _dialog() -> None:
        st.write("Cadastre seu nome.")
        new_name = st.text_input(
            "Nome",
            max_chars=20,
            placeholder="Seu nome",
            key="register_name",
        )
        if st.button("Cadastrar", key="dialog_register_btn", use_container_width=True):
            valid, clean_name, message = validate_new_name(new_name, names)
            if not valid:
                st.error(message)
                return

            new_participant = {
                "nome": clean_name,
                "pontos": 0,
                "finalistas": {str(i): None for i in range(1, 5)},
                "palpites": [empty_palpite(game_id) for game_id in jogo_ids()],
            }
            data["participantes"].append(new_participant)
            save_participantes(data, only_names=[clean_name])
            login_as(clean_name, show_mobile_rules=True)

    _dialog()


def render_login() -> None:
    data = load_participantes()
    names = participant_names(data)
    trophy_src = image_data_uri(FLAGS_DIR / "trofeu.webp", crop_alpha=True)
    trophy_html = (
        f'<img src="{trophy_src}" alt="Troféu">'
        if trophy_src
        else ""
    )

    with st.container(key="login_shell"):
        st.markdown(
            f'<div class="login-title">{trophy_html}<span>Bolão Copa 2026</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="login-heading">Login</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="login-help">Se já foi cadastrado, selecione seu nome para Entrar, caso contrário, clique em Cadastrar.</div>',
            unsafe_allow_html=True,
        )

        login_cols = st.columns([0.7, 0.3], gap="medium")
        with login_cols[0]:
            selected_name = st.selectbox(
                "Entrar",
                names,
                index=None,
                placeholder="Selecione seu nome",
                key="login_select",
                label_visibility="collapsed",
            )
        with login_cols[1]:
            if st.button(
                "Entrar",
                key="login_enter_btn",
                use_container_width=True,
                disabled=not bool(selected_name),
            ):
                login_as(selected_name)

        if st.button("Cadastrar", key="login_register_btn", use_container_width=True):
            register_dialog(data, names)

        st.write("")
        render_dashboard_button("login_dashboard")


def render_action_card(
    title: str,
    complete: bool,
    enabled: bool,
    enabled_text: str,
    disabled_text: str,
    page: str,
    key: str,
) -> None:
    if enabled:
        status_text = "✅ Concluído" if complete else "⚠️ Pendente"
        verb = "Editar" if complete else "Preencher"
        label = f"{verb} {title} · {status_text}"
    else:
        label = f"{title} · 🚫 Bloqueado"

    clicked = st.button(
        label,
        key=key,
        use_container_width=True,
        disabled=not enabled,
    )
    if clicked:
        go_to(page)

    st.markdown(
        f'<div class="action-note">{enabled_text if enabled else disabled_text}</div>',
        unsafe_allow_html=True,
    )


def render_mobile_rules_dialog() -> None:
    if not (is_mobile_client() and st.session_state.get("mobile_rules_pending")):
        return

    @st.dialog("Regras")
    def _dialog() -> None:
        st.markdown(read_regras())
        if st.button("Entendi", key="mobile_rules_ok", use_container_width=True):
            st.session_state["mobile_rules_pending"] = False
            rerun()

    _dialog()


def render_principal() -> None:
    data = load_participantes()
    participant = current_participant(data)
    if participant is None:
        st.session_state["page"] = "login"
        rerun()

    render_mobile_rules_dialog()

    now = datetime.now(TZ)
    with st.container(key="principal_shell"):
        st.markdown('<div class="principal-eyebrow">Área do Participante</div>', unsafe_allow_html=True)
        st.markdown('<div class="principal-title">Seus palpites</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="principal-subtitle">Escolha uma etapa para preencher ou revisar quando estiver liberada.</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="top-user">
                <div class="top-user-label">Participante</div>
                <div class="user-name">{participant['nome']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        render_action_card(
            "Fase de Grupos",
            complete=is_group_complete(participant),
            enabled=now < GROUP_DEADLINE,
            enabled_text="Disponível até 11/06/2026 às 16:00.",
            disabled_text="Prazo encerrado em 11/06/2026 às 16:00.",
            page="grupos",
            key="action_groups",
        )

        render_action_card(
            "Finalistas",
            complete=is_finalistas_complete(participant),
            enabled=FINALISTAS_START <= now < FINALISTAS_END,
            enabled_text="Disponível de 24/06/2026 às 01:00 até 28/06/2026 às 16:00.",
            disabled_text="Disponível somente de 24/06/2026 às 01:00 até 28/06/2026 às 16:00.",
            page="finalistas",
            key="action_finalistas",
        )

        render_action_card(
            "Eliminatórias",
            complete=is_eliminatorias_complete(participant),
            enabled=ELIMINATORIAS_START <= now < ELIMINATORIAS_END,
            enabled_text="Disponível de 24/06/2026 às 01:00 até 18/07/2026 às 18:00.",
            disabled_text="Disponível somente de 24/06/2026 às 01:00 até 18/07/2026 às 18:00.",
            page="eliminatorias",
            key="action_eliminatorias",
        )

        st.write("")
        render_dashboard_button("principal_dashboard")


def initialize_group_draft(participant: dict[str, Any]) -> None:
    owner = participant["nome"]
    if st.session_state.get("group_draft_owner") == owner:
        return

    guesses = get_guess_map(participant)
    group_games = load_jogos().query("Fase == 'Grupo'")
    for _, game in group_games.iterrows():
        game_id = game["Id"]
        guess = guesses.get(game_id, {})
        st.session_state[f"group_{game_id}_gols1"] = (
            "" if guess.get("gols1") is None else str(guess.get("gols1"))
        )
        st.session_state[f"group_{game_id}_gols2"] = (
            "" if guess.get("gols2") is None else str(guess.get("gols2"))
        )
        st.session_state[f"group_{game_id}_jogador"] = guess.get("jogador") or ""
    st.session_state["group_draft_owner"] = owner


def save_group_predictions(participant_name: str) -> tuple[bool, list[str]]:
    data = load_participantes()
    participant = next(
        (
            item
            for item in data.get("participantes", [])
            if item.get("nome") == participant_name
        ),
        None,
    )
    if participant is None:
        return False, ["Participante não encontrado."]

    errors: list[str] = []
    updates: dict[str, dict[str, Any]] = {}
    group_games = load_jogos().query("Fase == 'Grupo'")

    for _, game in group_games.iterrows():
        game_id = game["Id"]
        raw_gols1 = st.session_state.get(f"group_{game_id}_gols1", "")
        raw_gols2 = st.session_state.get(f"group_{game_id}_gols2", "")
        gols1, error1 = parse_goal(raw_gols1)
        gols2, error2 = parse_goal(raw_gols2)

        if error1:
            errors.append(f"{game_id}: placar de {game['Time1']} inválido. {error1}")
        if error2:
            errors.append(f"{game_id}: placar de {game['Time2']} inválido. {error2}")

        player = st.session_state.get(f"group_{game_id}_jogador") or None
        if not is_brazil_game(game):
            player = None

        updates[game_id] = {
            "gols1": gols1,
            "gols2": gols2,
            "resultado": result_from_score(gols1, gols2),
            "jogador": player,
        }

    if errors:
        return False, errors

    for guess in participant["palpites"]:
        if guess["jogo"] in updates:
            guess.update(updates[guess["jogo"]])

    save_participantes(data, only_names=[participant_name])
    return True, []


def confirm_back_dialog() -> None:
    dialog = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)

    def body() -> None:
        st.write("As alterações não foram salvas, quer mesmo sair?")
        yes, no = st.columns(2)
        if yes.button("Sim", use_container_width=True):
            st.session_state["group_draft_owner"] = None
            st.session_state["page"] = "principal"
            rerun()
        if no.button("Não", use_container_width=True):
            st.session_state["confirm_group_back"] = False
            rerun()

    if dialog is not None:
        dialog("Voltar sem salvar")(body)()
    else:
        st.warning("As alterações não foram salvas, quer mesmo sair?")
        yes, no = st.columns(2)
        if yes.button("Sim", use_container_width=True):
            st.session_state["group_draft_owner"] = None
            st.session_state["page"] = "principal"
            rerun()
        if no.button("Não", use_container_width=True):
            st.session_state["confirm_group_back"] = False
            rerun()


def render_save_errors(errors: list[str]) -> None:
    st.error("Corrija os campos inválidos antes de salvar.")
    for error in errors[:8]:
        st.caption(error)
    if len(errors) > 8:
        st.caption(f"E mais {len(errors) - 8} erro(s).")


def confirm_save_dialog(participant_name: str) -> None:
    dialog = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)

    def body() -> None:
        st.markdown(
            f"Tem certeza que deseja editar e salvar como participante **{participant_name}**?"
        )
        yes, no = st.columns(2)
        if yes.button("Sim", type="primary", use_container_width=True):
            ok, errors = save_group_predictions(participant_name)
            if ok:
                st.session_state["group_draft_owner"] = None
                st.session_state["confirm_group_back"] = False
                st.session_state["page"] = "principal"
                rerun()
            render_save_errors(errors)
        if no.button("Não", use_container_width=True):
            rerun()

    if dialog is not None:
        dialog("Confirmar salvamento")(body)()
    else:
        st.warning(
            f"Tem certeza que deseja editar e salvar como participante **{participant_name}**?"
        )
        yes, no = st.columns(2)
        if yes.button("Sim", type="primary", use_container_width=True):
            ok, errors = save_group_predictions(participant_name)
            if ok:
                st.session_state["group_draft_owner"] = None
                st.session_state["confirm_group_back"] = False
                st.session_state["page"] = "principal"
                rerun()
            render_save_errors(errors)
        if no.button("Não", use_container_width=True):
            rerun()


def render_groups() -> None:
    data = load_participantes()
    participant = current_participant(data)
    if participant is None:
        go_to("login")

    if datetime.now(TZ) >= GROUP_DEADLINE:
        st.warning("O prazo para preencher a fase de grupos já encerrou.")
        if st.button("Voltar", use_container_width=True):
            go_to("principal")
        return

    initialize_group_draft(participant)

    jogadores = sorted(set(load_jogadores()["Nome"].tolist()))
    player_options = [""] + jogadores
    group_games = load_jogos().query("Fase == 'Grupo'").copy()

    with st.container(key="group_actions_bar"):
        actions = st.columns(2)
        if actions[0].button("Salvar", type="primary", use_container_width=True):
            st.session_state["confirm_group_back"] = False
            confirm_save_dialog(participant["nome"])

        if actions[1].button("Voltar", use_container_width=True):
            st.session_state["confirm_group_back"] = True

    if st.session_state.get("confirm_group_back"):
        confirm_back_dialog()

    with st.container(key="groups_shell"):
        st.markdown('<div class="groups-title">Fase de Grupos</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="groups-participant">Participante: <strong>{participant["nome"]}</strong></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="groups-list-start"></div>', unsafe_allow_html=True)

        for group in sorted(group_games["Id"].str[0].unique()):
            games_in_group = group_games[group_games["Id"].str.startswith(group)]
            with st.expander(f"Grupo {group}", expanded=False):
                for _, game in games_in_group.iterrows():
                    with st.container(border=True):
                        st.markdown(
                            f"""
                            <div class="match-meta">
                                {format_datetime(game['Data'])}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        render_match_score_line(game)

                        if is_brazil_game(game):
                            current_player = st.session_state.get(f"group_{game['Id']}_jogador", "")
                            index = (
                                player_options.index(current_player)
                                if current_player in player_options
                                else 0
                            )
                            st.selectbox(
                                "Nome do Brasileiro que fará gol",
                                player_options,
                                index=index,
                                key=f"group_{game['Id']}_jogador",
                                placeholder="Selecione um jogador",
                            )


def render_blank_page(title: str) -> None:
    st.title(title)
    if st.button("Voltar", use_container_width=True):
        if st.session_state.get("participant_name"):
            go_to("principal")
        go_to("login")


def main() -> None:
    st.session_state.setdefault("page", "login")
    st.session_state.setdefault("participant_name", None)
    st.session_state.setdefault("confirm_group_back", False)
    st.session_state.setdefault("mobile_rules_pending", False)

    page = st.session_state["page"]
    show_sidebar = page in {"login", "principal"}
    apply_styles(show_sidebar)
    if show_sidebar:
        render_sidebar()

    if page == "login":
        render_login()
    elif page == "principal":
        render_principal()
    elif page == "grupos":
        render_groups()
    elif page == "finalistas":
        render_blank_page("Finalistas")
    elif page == "eliminatorias":
        render_blank_page("Eliminatórias")
    elif page == "dashboard":
        render_blank_page("Jogos e Ranking")
    else:
        st.session_state["page"] = "login"
        rerun()


if __name__ == "__main__":
    main()
