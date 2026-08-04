"""
ProduktifAI - Personal Productivity & Data Assistant
Final Project: LLM-Based Tools and Gemini API Integration for Data Scientists (Hacktiv8)

Chatbot ini membantu user mengelola to-do list dan catatan pribadi lewat
percakapan natural, menggunakan LLM (Llama via Groq) dengan Function Calling.

Keterbatasan yang disengaja (out of scope):
- Tidak ada persistensi data antar sesi (data hilang saat halaman di-refresh).
- Tidak ada autentikasi user; semua data tersimpan di session browser yang sama.
- Context window dibatasi MAX_HISTORY pesan terakhir untuk mencegah token overflow.
"""

# --- Imports ---
import json
import os
import re

import streamlit as st
from groq import Groq

# --- Konfigurasi halaman ---
st.set_page_config(page_title="ProduktifAI", page_icon="assets/icon-title.png", layout="centered")

# --- Konstanta ---
MODEL = "llama-3.3-70b-versatile"
MAX_HISTORY = 20  # jumlah pesan non-system yang dikirim ke model (mencegah context overflow)

SYSTEM_PROMPT = """Kamu adalah ProduktifAI, asisten produktivitas pribadi berbahasa Indonesia.
Gaya bicaramu santai, ramah, tapi tetap jelas dan to the point.

Creator mu adalah "Adam Marchelino"

Tugasmu:
1. Membantu user mengelola to-do list: menambah tugas, menandai tugas selesai/belum selesai, dan menampilkan daftar tugas.
2. Membantu user menyimpan catatan singkat.
3. Menjawab pertanyaan seputar produktivitas, manajemen waktu, dan prioritas kerja dengan saran yang praktis.

Aturan penting:
- Kalau user minta menambah tugas, menyelesaikan tugas, membatalkan/undo tugas, menghapus tugas/catatan, menyimpan catatan, atau melihat daftar tugas/catatan, WAJIB pakai tools yang tersedia. Jangan cuma balas teks tanpa memanggil tool.
- Setelah tool dijalankan, konfirmasi hasilnya ke user dengan bahasa yang natural dan singkat.
- Kalau user cuma ngobrol atau nanya hal umum, jawab langsung tanpa perlu tool.
- WAJIB gunakan format tool call resmi dari API. DILARANG KERAS mengarang format teks seperti <function=...>, <tool_call>, atau format JSON mentah apapun sebagai balasan teks. Kalau tool tidak tersedia, katakan terus terang bahwa fitur itu belum ada.

Aturan membedakan add_task vs add_note:
- Gunakan add_task kalau kalimat user mengandung instruksi/aksi yang harus dikerjakan di masa depan. Kata kunci: "ingetin", "tambahin tugas", "aku harus", "jangan lupa [kerjakan]", "tolong kerjain", "bikin", "selesaikan".
- Gunakan add_note kalau kalimat user berupa informasi/fakta yang cukup disimpan sebagai referensi, tanpa ada aksi yang perlu "diselesaikan". Kata kunci: "catet", "simpen", "FYI", "info", atau kalimat berupa fakta/data.
- Kalau ambigu (tidak jelas apakah tugas atau catatan), tanya balik ke user dengan satu kalimat singkat untuk klarifikasi. JANGAN menebak dan langsung memanggil tool.

Aturan undo/batalkan tugas:
- Kalau user minta "batalkan", "undo", "kembalikan jadi belum selesai", atau sejenisnya untuk suatu tugas → WAJIB panggil uncomplete_task. JANGAN panggil complete_task dan JANGAN mengarang format apapun.

Aturan hapus tugas/catatan:
- Kalau user minta hapus satu tugas → panggil delete_task(task_number=...).
- Kalau user minta hapus satu catatan → panggil delete_note(note_number=...).

Contoh (few-shot):
User: "ingetin aku buat ngumpulin laporan besok" → panggil add_task(task="ngumpulin laporan besok")
User: "tambahin tugas: review PR dari Budi" → panggil add_task(task="review PR dari Budi")
User: "tugas 1 udah selesai" → panggil complete_task(task_number=1)
User: "eh tugas 1 belum selesai ternyata, undo dong" → panggil uncomplete_task(task_number=1)
User: "hapus tugas nomor 2" → panggil delete_task(task_number=2)
User: "catet ya, password WiFi kantor itu ProduktifAI123" → panggil add_note(note="password WiFi kantor: ProduktifAI123")
User: "FYI, meeting minggu depan dipindah ke Selasa" → panggil add_note(note="meeting minggu depan dipindah ke Selasa")
User: "hapus catatan nomor 1" → panggil delete_note(note_number=1)
"""

# --- Definisi Tools (Function Calling) ---
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": "Menambahkan satu tugas baru ke to-do list milik user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Deskripsi singkat tugas yang ingin ditambahkan."}
                },
                "required": ["task"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Menandai satu tugas sebagai selesai berdasarkan nomor urutnya.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_number": {"type": "integer", "description": "Nomor urut tugas (dimulai dari 1) yang ingin ditandai selesai."}
                },
                "required": ["task_number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "uncomplete_task",
            "description": "Mengembalikan status tugas menjadi belum selesai (undo complete). Gunakan ini kalau user minta batalkan/undo penyelesaian tugas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_number": {"type": "integer", "description": "Nomor urut tugas (dimulai dari 1) yang ingin dikembalikan ke status belum selesai."}
                },
                "required": ["task_number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Menghapus satu tugas dari to-do list berdasarkan nomor urutnya.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_number": {"type": "integer", "description": "Nomor urut tugas (dimulai dari 1) yang ingin dihapus."}
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
                    "note": {"type": "string", "description": "Isi catatan yang ingin disimpan."}
                },
                "required": ["note"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_note",
            "description": "Menghapus satu catatan berdasarkan nomor urutnya.",
            "parameters": {
                "type": "object",
                "properties": {
                    "note_number": {"type": "integer", "description": "Nomor urut catatan (dimulai dari 1) yang ingin dihapus."}
                },
                "required": ["note_number"],
            },
        },
    },
]


# --- Fungsi-fungsi tools ---
def _validate_index(number: int, collection: list, label: str) -> tuple[int, str | None]:
    """Validasi nomor urut dan kembalikan (idx, error_message). idx=-1 jika tidak valid."""
    idx = int(number) - 1
    if idx < 0 or idx >= len(collection):
        return -1, f"Nomor {label} {number} tidak ditemukan (total {label}: {len(collection)})."
    return idx, None


def add_task(task: str) -> str:
    """Tambahkan tugas baru ke session_state.tasks."""
    st.session_state.tasks.append({"task": task, "done": False})
    return f"Tugas '{task}' berhasil ditambahkan ke to-do list."


def complete_task(task_number: int) -> str:
    """Tandai tugas pada nomor urut tertentu sebagai selesai."""
    idx, err = _validate_index(task_number, st.session_state.tasks, "tugas")
    if err:
        return err
    st.session_state.tasks[idx]["done"] = True
    return f"Tugas '{st.session_state.tasks[idx]['task']}' ditandai selesai."


def uncomplete_task(task_number: int) -> str:
    """Kembalikan status tugas ke belum selesai (undo complete)."""
    idx, err = _validate_index(task_number, st.session_state.tasks, "tugas")
    if err:
        return err
    st.session_state.tasks[idx]["done"] = False
    return f"Tugas '{st.session_state.tasks[idx]['task']}' dikembalikan ke status belum selesai."


def delete_task(task_number: int) -> str:
    """Hapus tugas pada nomor urut tertentu dari to-do list."""
    idx, err = _validate_index(task_number, st.session_state.tasks, "tugas")
    if err:
        return err
    removed = st.session_state.tasks.pop(idx)
    return f"Tugas '{removed['task']}' berhasil dihapus."


def list_tasks() -> str:
    """Kembalikan string daftar semua tugas beserta statusnya."""
    tasks = st.session_state.tasks
    if not tasks:
        return "To-do list masih kosong."
    lines = []
    for i, t in enumerate(tasks, start=1):
        status = "✅" if t["done"] else "⬜"
        lines.append(f"{i}. {status} {t['task']}")
    return "\n".join(lines)


def add_note(note: str) -> str:
    """Simpan catatan baru ke session_state.notes."""
    st.session_state.notes.append(note)
    return "Catatan berhasil disimpan."


def delete_note(note_number: int) -> str:
    """Hapus catatan pada nomor urut tertentu."""
    idx, err = _validate_index(note_number, st.session_state.notes, "catatan")
    if err:
        return err
    removed = st.session_state.notes.pop(idx)
    preview = removed[:40] + "..." if len(removed) > 40 else removed
    return f"Catatan '{preview}' berhasil dihapus."


AVAILABLE_FUNCTIONS = {
    "add_task": add_task,
    "complete_task": complete_task,
    "uncomplete_task": uncomplete_task,
    "delete_task": delete_task,
    "list_tasks": list_tasks,
    "add_note": add_note,
    "delete_note": delete_note,
}

# Pola regex untuk mendeteksi pseudo function-call yang dihalusinasi model
_HALLUCINATION_PATTERNS = [
    re.compile(r"<function=\w+>"),
    re.compile(r"<tool_call>"),
    re.compile(r"</function>"),
    re.compile(r'"name"\s*:\s*"\w+"\s*,\s*"arguments"\s*:'),
]


# --- Fungsi helper ---
def detect_hallucinated_tool_call(text: str) -> bool:
    """Deteksi apakah teks mengandung pseudo function-call yang dihalusinasi model."""
    return any(p.search(text) for p in _HALLUCINATION_PATTERNS)


def is_tool_call_error(error: Exception) -> bool:
    """Cek apakah error berasal dari kegagalan pemanggilan tool."""
    error_text = str(error).lower()
    return (
        "tool_use_failed" in error_text
        or "failed to call a function" in error_text
        or "tool_call" in error_text
    )


def build_messages_for_api() -> list:
    """Ambil system prompt + MAX_HISTORY pesan terakhir untuk dikirim ke API."""
    system_msg = st.session_state.messages[0]
    history = st.session_state.messages[1:]
    trimmed = history[-MAX_HISTORY:]
    return [system_msg] + trimmed


def ask_model(client, messages, use_tools: bool = True):
    """Kirim pesan ke model Groq dan kembalikan response-nya."""
    kwargs = {"model": MODEL, "messages": messages, "temperature": 0.2}
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
                    "content": "Jika format tool call tidak valid, jawab user secara natural tanpa tool.",
                }
            ]
            return client.chat.completions.create(model=MODEL, messages=fallback_messages, temperature=0.2)
        raise


# --- CSS base ---
CSS_BASE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
</style>
"""


# --- Inisialisasi session_state ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "notes" not in st.session_state:
    st.session_state.notes = []

st.markdown(CSS_BASE, unsafe_allow_html=True)


# --- Sidebar ---
with st.sidebar:
    # Keamanan API Key: pakai secrets/env kalau ada, jangan tampilkan input ke user
    _secret_key = st.secrets.get("GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
    if _secret_key:
        api_key = _secret_key
    else:
        api_key = st.text_input("Groq API Key", type="password", placeholder="Masukkan API key kamu...")
        st.caption("Dapatkan API key gratis di [console.groq.com](https://console.groq.com/)")

    # To-Do List: pisahkan tugas belum selesai dan sudah selesai
    st.header("📋 To-Do List")
    if st.session_state.tasks:
        pending = [(i, t) for i, t in enumerate(st.session_state.tasks, start=1) if not t["done"]]
        done_tasks = [(i, t) for i, t in enumerate(st.session_state.tasks, start=1) if t["done"]]

        for i, t in pending:
            st.markdown(f"⬜ {i}. {t['task']}")

        if done_tasks:
            st.caption("Selesai")
            st.divider()
            for i, t in done_tasks:
                st.markdown(f"✅ ~~{i}. {t['task']}~~")
    else:
        st.caption("Belum ada tugas.")

    st.divider()

    # Catatan: tampilkan sebagai kartu vertikal
    st.header("📝 Catatan")
    if st.session_state.notes:
        for i, note in enumerate(st.session_state.notes, start=1):
            with st.container(border=True):
                if len(note) > 80:
                    st.markdown(f"**#{i}** {note[:60]}...")
                    with st.expander("Lihat selengkapnya"):
                        st.write(note)
                else:
                    st.markdown(f"**#{i}** {note}")
    else:
        st.caption("Belum ada catatan.")

    st.divider()
    if st.button("🔄 Reset Percakapan & Data"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.session_state.tasks = []
        st.session_state.notes = []
        st.rerun()


# --- Main chat area ---
st.title("📝 Notewell")
st.caption("Sampaikan saja lewat percakapan, Notewell akan membantu mencatat tugas dan menyimpan catatan Anda dengan otomatis.")


if not api_key:
    st.warning("Masukkan Groq API Key di sidebar dulu untuk mulai chat.")
    st.stop()


@st.cache_resource
def get_client(key: str) -> Groq:
    return Groq(api_key=key)


client = get_client(api_key)

# Tampilkan riwayat chat (skip system message dan tool message)
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
            try:
                # Langkah 1: kirim pesan + tools ke model
                api_messages = build_messages_for_api()
                response = ask_model(client, api_messages, use_tools=True)
                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls

                if tool_calls:
                    # Simpan pesan assistant yang berisi tool_calls ke history
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
                            parsed = json.loads(tc.function.arguments)
                            fn_args = parsed if isinstance(parsed, dict) else {}
                        except (json.JSONDecodeError, ValueError):
                            result = f"Tool {fn_name} mengirim argumen yang tidak valid."
                        else:
                            fn = AVAILABLE_FUNCTIONS.get(fn_name)
                            result = fn(**fn_args) if fn else f"Tool '{fn_name}' tidak dikenal. Fitur ini belum tersedia."

                        st.session_state.messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "name": fn_name,
                                "content": result,
                            }
                        )

                    # Langkah 2: minta model rangkum hasil tool jadi jawaban natural
                    followup = ask_model(client, build_messages_for_api(), use_tools=False)
                    final_reply = followup.choices[0].message.content
                    st.session_state.messages.append({"role": "assistant", "content": final_reply})
                else:
                    final_reply = response_message.content
                    st.session_state.messages.append({"role": "assistant", "content": final_reply})

                # Jaring pengaman: deteksi halusinasi tool call dalam teks
                if detect_hallucinated_tool_call(final_reply):
                    final_reply = "Maaf, ada kendala teknis saat memproses permintaan ini. Bisa dicoba ulang dengan kalimat yang lebih spesifik?"

            except Exception as e:
                error_msg = str(e).lower()
                if "invalid api key" in error_msg or "authentication" in error_msg:
                    final_reply = "API Key tidak valid. Pastikan Groq API Key kamu sudah benar di sidebar."
                elif "rate limit" in error_msg or "quota" in error_msg:
                    final_reply = "Kuota API habis atau terlalu banyak request. Coba lagi beberapa saat."
                elif "connection" in error_msg or "timeout" in error_msg:
                    final_reply = "Gagal terhubung ke server. Periksa koneksi internet kamu."
                else:
                    final_reply = f"Terjadi kesalahan: {e}"

            st.markdown(final_reply)
