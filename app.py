"""
ProduktifAI - Personal Productivity & Data Assistant
Final Project: LLM-Based Tools and Gemini API Integration for Data Scientists (Hacktiv8)

Chatbot ini membantu user mengelola to-do list dan catatan pribadi lewat
percakapan natural, menggunakan LLM (Llama via Groq) dengan Function Calling.
"""

import json
import os

import streamlit as st
from groq import Groq

# Konfigurasi halaman
st.set_page_config(page_title="ProduktifAI", page_icon="🗂️", layout="centered")

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Kamu adalah ProduktifAI, asisten produktivitas pribadi berbahasa Indonesia.
Gaya bicaramu santai, ramah, tapi tetap jelas dan to the point.

Creator mu adalah "Adam Marchelino"

Tugasmu:
1. Membantu user mengelola to-do list: menambah tugas, menandai tugas selesai, dan menampilkan daftar tugas.
2. Membantu user menyimpan catatan singkat.
3. Menjawab pertanyaan seputar produktivitas, manajemen waktu, dan prioritas kerja dengan saran yang praktis.

Aturan penting:
- Kalau user minta menambah tugas, menyelesaikan tugas, menyimpan catatan, atau melihat daftar tugas/catatan, WAJIB pakai tools yang tersedia. Jangan cuma balas teks tanpa memanggil tool.
- Setelah tool dijalankan, konfirmasi hasilnya ke user dengan bahasa yang natural dan singkat.
- Kalau user cuma ngobrol atau nanya hal umum, jawab langsung tanpa perlu tool.
- Kalau kamu memakai tool, gunakan format tool call resmi dari API. Jangan pakai format custom seperti <function=...> atau tag XML.
"""

# Definisi Tools (Function Calling)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": "Menambahkan satu tugas baru ke to-do list milik user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "Deskripsi singkat tugas yang ingin ditambahkan.",
                    }
                },
                "required": ["task"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Menandai satu tugas sebagai selesai berdasarkan nomor urutnya di to-do list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_number": {
                        "type": "integer",
                        "description": "Nomor urut tugas (dimulai dari 1) yang ingin ditandai selesai.",
                    }
                },
                "required": ["task_number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "Menampilkan seluruh isi to-do list beserta statusnya (selesai/belum).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_note",
            "description": "Menyimpan satu catatan singkat dari user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "note": {
                        "type": "string",
                        "description": "Isi catatan yang ingin disimpan.",
                    }
                },
                "required": ["note"],
            },
        },
    },
]


# Implementasi fungsi tools (jalan di session_state Streamlit)
def add_task(task: str) -> str:
    st.session_state.tasks.append({"task": task, "done": False})
    return f"Tugas '{task}' berhasil ditambahkan ke to-do list."


def complete_task(task_number: int) -> str:
    idx = int(task_number) - 1
    tasks = st.session_state.tasks
    if 0 <= idx < len(tasks):
        tasks[idx]["done"] = True
        return f"Tugas '{tasks[idx]['task']}' ditandai selesai."
    return f"Nomor tugas {task_number} tidak ditemukan di to-do list."


def list_tasks() -> str:
    tasks = st.session_state.tasks
    if not tasks:
        return "To-do list masih kosong."
    lines = []
    for i, t in enumerate(tasks, start=1):
        status = "✅" if t["done"] else "⬜"
        lines.append(f"{i}. {status} {t['task']}")
    return "\n".join(lines)


def add_note(note: str) -> str:
    st.session_state.notes.append(note)
    return "Catatan berhasil disimpan."


AVAILABLE_FUNCTIONS = {
    "add_task": add_task,
    "complete_task": complete_task,
    "list_tasks": list_tasks,
    "add_note": add_note,
}


def is_tool_call_error(error: Exception) -> bool:
    error_text = str(error).lower()
    return (
        "tool_use_failed" in error_text
        or "failed to call a function" in error_text
        or "tool_call" in error_text
    )


def ask_model(client, messages, use_tools: bool = True):
    kwargs = {"model": MODEL, "messages": messages, "temperature": 0.4}

    if use_tools:
        kwargs["tools"] = TOOLS
        kwargs["tool_choice"] = "auto"

    try:
        return client.chat.completions.create(**kwargs)
    except Exception as error:
        if use_tools and is_tool_call_error(error):
            fallback_messages = messages + [
                {
                    "role": "system",
                    "content": "Jika format tool call tidak valid, jawab user secara natural tanpa tool. Jangan pakai format custom seperti <function=...>.",
                }
            ]
            return client.chat.completions.create(model=MODEL, messages=fallback_messages, temperature=0.4)
        raise


# Session state
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "notes" not in st.session_state:
    st.session_state.notes = []

# Sidebar: API Key + Data View
with st.sidebar:
    # st.header("⚙️ Pengaturan")

    # default_key = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
    # api_key = st.text_input("Groq API Key", value=default_key, type="password")
    # st.caption("Dapatkan API key gratis di [console.groq.com](https://console.groq.com/)")

    # st.divider()
    st.header("📋 To-Do List")
    if st.session_state.tasks:
        for i, t in enumerate(st.session_state.tasks, start=1):
            st.checkbox(f"{i}. {t['task']}", value=t["done"], key=f"task_{i}", disabled=True)
    else:
        st.caption("Belum ada tugas.")

    st.divider()
    st.header("📝 Catatan")
    if st.session_state.notes:
        for i, n in enumerate(st.session_state.notes, start=1):
            st.markdown(f"{i}. {n}")
    else:
        st.caption("Belum ada catatan.")

    st.divider()
    if st.button("🔄 Reset Percakapan & Data"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.session_state.tasks = []
        st.session_state.notes = []
        st.rerun()

# Header
st.title("🗂️ ProduktifAI")
st.caption("Asisten produktivitas pribadi — kelola tugas & catatan langsung lewat chat")

if not api_key:
    st.warning("Masukkan Groq API Key di sidebar dulu untuk mulai chat.")
    st.stop()

client = Groq(api_key=api_key)

# Tampilkan riwayat chat (skip system message)
for msg in st.session_state.messages:
    if msg["role"] in ("user", "assistant") and msg.get("content"):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Input chat
prompt = st.chat_input("Contoh: 'tambahin tugas belajar RAG' atau 'tugas apa aja yang belum selesai?'")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("ProduktifAI lagi mikir..."):
            # Langkah 1: kirim pesan + tools ke model
            response = ask_model(client, st.session_state.messages, use_tools=True)
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                # Simpan pesan assistant yang berisi tool_calls
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": response_message.content or "",
                        "tool_calls": [tc.model_dump() for tc in tool_calls],
                    }
                )

                # Jalankan setiap tool yang diminta model
                for tc in tool_calls:
                    fn_name = tc.function.name
                    try:
                        fn_args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        result = f"Tool {fn_name} mengirim argumen yang tidak valid."
                    else:
                        fn = AVAILABLE_FUNCTIONS.get(fn_name)
                        result = fn(**fn_args) if fn else f"Tool {fn_name} tidak dikenal."

                    st.session_state.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": fn_name,
                            "content": result,
                        }
                    )

                # Langkah 2: minta model rangkum hasil tool jadi jawaban natural
                followup = ask_model(client, st.session_state.messages, use_tools=False)
                final_reply = followup.choices[0].message.content
            else:
                final_reply = response_message.content
                st.session_state.messages.append({"role": "assistant", "content": final_reply})

            st.markdown(final_reply)

    # Pastikan balasan akhir tersimpan di history sebagai assistant message biasa
    if tool_calls:
        st.session_state.messages.append({"role": "assistant", "content": final_reply})

    st.rerun()
