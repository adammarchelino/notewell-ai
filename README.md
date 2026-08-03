# ProduktifAI — Personal Productivity & Data Assistant

Final Project: **LLM-Based Tools and Gemini API Integration for Data Scientists** (Hacktiv8)

## Use Case

ProduktifAI adalah chatbot asisten produktivitas pribadi. Lewat percakapan natural (bahasa Indonesia,
gaya santai), user bisa:

- Menambahkan tugas ke to-do list
- Menandai tugas sebagai selesai
- Melihat daftar tugas beserta statusnya
- Menyimpan catatan singkat
- Bertanya seputar manajemen waktu / prioritas kerja dan dapat saran dari LLM

## Parameter Kreatif

- **Gaya bahasa**: santai, ramah, bahasa Indonesia
- **Function Calling**: model (Llama 3.3 70B via Groq) memutuskan sendiri kapan harus memanggil
  tool `add_task`, `complete_task`, `list_tasks`, atau `add_note` berdasarkan permintaan user
- **Memory**: riwayat percakapan disimpan selama sesi berjalan (`st.session_state`)
- **Data view**: to-do list dan catatan ditampilkan real-time di sidebar

## Tech Stack

- [Streamlit](https://streamlit.io/) — UI web interaktif
- [Groq API](https://console.groq.com/) — akses model Llama 3.3 70B, mendukung function calling

## Cara Menjalankan Lokal

1. Clone repo ini dan masuk ke foldernya
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Buat akun & API key di https://console.groq.com/ (menu API Keys → Create API Key)
4. Jalankan app:
   ```bash
   streamlit run app.py
   ```
5. Masukkan Groq API Key di sidebar aplikasi (atau isi lewat `.streamlit/secrets.toml`, contoh ada
   di `.streamlit/secrets.toml.example`)

## Cara Deploy ke Streamlit Cloud

1. Push project ini ke repo GitHub kamu
2. Buka https://share.streamlit.io/ dan login
3. Klik "New app", pilih repo ini, dan set `app.py` sebagai entry point
4. Di menu **Advanced settings → Secrets**, tambahkan:
   ```toml
   GROQ_API_KEY = "api_key_kamu"
   ```
5. Deploy — aplikasi akan dapat URL publik

## Contoh Percakapan

```
User: tambahin tugas belajar RAG buat besok
Bot:  Oke, tugas "belajar RAG buat besok" udah aku tambahin ke to-do list kamu!

User: tugas apa aja yang masih belum selesai?
Bot:  Ini daftar tugas kamu:
      1. ⬜ belajar RAG buat besok

User: catet dong, groq API key jangan lupa disimpan aman
Bot:  Siap, catatan udah aku simpan!

User: gimana cara ngatur prioritas kerja kalau tugasnya numpuk?
Bot:  [saran dari LLM soal time management]
```

## Deliverables

- [ ] URL repositori GitHub
- [ ] Screenshot User Interface (chat + sidebar to-do list & catatan)
