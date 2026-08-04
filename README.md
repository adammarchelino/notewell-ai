# Notewell — Asisten Produktivitas Pribadi

Final Project: **LLM-Based Tools and Gemini API Integration for Data Scientists** (Hacktiv8)

## Use Case

Notewell adalah chatbot asisten produktivitas pribadi. Lewat percakapan natural (bahasa
Indonesia, gaya santai dan sopan), pengguna bisa:

- Menambahkan tugas ke to-do list
- Menandai tugas sebagai selesai
- Membatalkan status selesai suatu tugas (undo)
- Melihat daftar tugas beserta statusnya (dipisah antara yang belum & sudah selesai)
- Menyimpan catatan singkat
- Bertanya seputar manajemen waktu / prioritas kerja dan mendapat saran dari LLM

## Target Pengguna

Individu yang ingin mengelola tugas dan catatan harian secara lebih praktis, seperti
mahasiswa, pekerja, atau siapa saja dengan aktivitas padat yang membutuhkan cara cepat
mencatat tanpa harus membuka aplikasi to-do list terpisah. Notewell cocok bagi pengguna
yang lebih nyaman menyampaikan tugas dan catatan lewat percakapan natural dibandingkan
mengisi form atau input manual.

## Parameter Kreatif

- **Gaya bahasa**: santai, ramah, sopan, berbahasa Indonesia
- **Function Calling**: model LLM (Llama via Groq) memutuskan sendiri kapan harus
  memanggil tool `add_task`, `complete_task`, `uncomplete_task`, `list_tasks`, atau
  `add_note` berdasarkan maksud permintaan pengguna, termasuk membedakan mana yang
  merupakan tugas (butuh aksi) dan mana yang sekadar catatan (informasi/referensi)
- **Memory**: riwayat percakapan disimpan selama sesi berjalan (`st.session_state`)
- **Data view**: to-do list (dipisah belum selesai/selesai) dan catatan (tampilan kartu)
  ditampilkan real-time di sidebar
- **Keamanan API key**: kolom input API key hanya muncul kalau `GROQ_API_KEY` belum
  dikonfigurasi lewat secrets; kalau sudah dikonfigurasi (mis. saat deploy), kolom
  tersembunyi otomatis supaya key developer tidak bisa di-reveal pengguna lain

## Tech Stack

- [Streamlit](https://streamlit.io/) — UI web interaktif
- [Groq API](https://console.groq.com/) — akses model LLM open-source (Llama, dsb) dengan
  dukungan function calling. Cek [console.groq.com/docs/models](https://console.groq.com/docs/models)
  untuk daftar model yang aktif saat ini, karena Groq cukup sering memperbarui/
  mendeprecate model

## Cara Menjalankan Lokal

1. Clone repo ini dan masuk ke foldernya
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Buat akun & API key di https://console.groq.com/ (menu API Keys → Create API Key)
4. Salin `.streamlit/secrets.toml.example` menjadi `.streamlit/secrets.toml`, lalu isi:
   ```toml
   GROQ_API_KEY = "api_key_kamu"
   ```
5. Jalankan app:
   ```bash
   streamlit run app.py
   ```

## Cara Deploy ke Streamlit Cloud

1. Push project ini ke repo GitHub kamu (pastikan `.streamlit/secrets.toml` masuk
   `.gitignore`, jangan sampai ikut ter-push)
2. Buka https://share.streamlit.io/ dan login pakai akun GitHub
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

User: selesaikan tugas 1
Bot:  Tugas "belajar RAG buat besok" ditandai selesai.

User: eh tugas 1 undo jadi belum selesai
Bot:  Oke, tugas "belajar RAG buat besok" dikembalikan ke status belum selesai.

User: catet dong, groq API key jangan lupa disimpan aman
Bot:  Siap, catatan udah aku simpan!

User: gimana cara ngatur prioritas kerja kalau tugasnya numpuk?
Bot:  [saran dari LLM soal time management]
```

## Batasan yang Disengaja (Out of Scope)

- Data (tugas, catatan, riwayat chat) tersimpan di `st.session_state`, sehingga hilang
  saat sesi browser ditutup atau aplikasi restart. Persistensi lewat database (SQLite/
  Supabase) direncanakan sebagai pengembangan lanjutan di luar cakupan final project ini.
- Belum ada RAG (upload dokumen) atau integrasi MCP ke platform lain, disimpan sebagai
  pengembangan lanjutan agar scope final project tetap fokus dan stabil.
