# Ollama Setup Guide for MyGlot

This guide walks you through installing and configuring **Ollama** so MyGlot can use a local LLM for translation — with word-by-word explanations included.

> **Time:** ~5 minutes (plus model download time).
> **Cost:** free. Ollama runs entirely on your local machine.

---

## 0. What you'll end up with

- **Ollama** installed and running as a local server on port `11434`.
- A translation model (e.g. `translategemma:latest`) pulled and ready.
- MyGlot configured to use `ollama` as the translate provider.
- Translations that include a word-by-word / phrase-by-phrase **explanation** rendered as Markdown in the UI.

> **Note:** Ollama is a **translate-only** provider. TTS and STT still require Google Cloud (or the `fake` provider for offline dev). You can mix providers — e.g. Ollama for translation + Google for TTS/STT.

---

## 1. Install Ollama

### macOS

```bash
brew install ollama
```

Or download from <https://ollama.com/download/mac>.

### Linux

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows

Download from <https://ollama.com/download/windows>.

### Verify installation

```bash
ollama --version
```

---

## 2. Start the Ollama server

Ollama needs a running server process to serve model requests.

```bash
ollama serve
```

This starts the server on `http://localhost:11434` by default. Keep this terminal open, or run it in the background.

> **Tip:** On macOS, if you installed Ollama via the desktop app, the server starts automatically when you open the app. You can check with:
> ```bash
> curl -s http://localhost:11434/ | head -1
> ```
> Expected output: `Ollama is running`

---

## 3. Pull a translation model

MyGlot defaults to `translategemma:latest`, a model tuned for translation tasks:

```bash
ollama pull translategemma:latest
```

This downloads the model (~2–5 GB depending on the variant). Wait for the download to complete.

### Alternative models

Any Ollama model that can follow instructions will work. Some options:

| Model | Size | Notes |
|-------|------|-------|
| `translategemma:latest` | ~2 GB | Recommended — optimised for translation |
| `gemma3:4b` | ~3 GB | General-purpose, good at translation |
| `llama3.2:3b` | ~2 GB | Lightweight general-purpose |
| `mistral` | ~4 GB | Good instruction-following |

To use a different model, set `MYGLOT_OLLAMA_MODEL` in your `.env` (see step 4).

### Verify the model works

```bash
ollama run translategemma:latest "Translate 'Good morning' to German"
```

You should see a German translation in the output.

---

## 4. Configure MyGlot to use Ollama

Edit `.env` in the project root (copy from `.env.example` if it doesn't exist):

```dotenv
# Switch the translate provider to Ollama
MYGLOT_TRANSLATE_PROVIDER=ollama

# Ollama server URL (default: http://localhost:11434)
MYGLOT_OLLAMA_BASE_URL=http://localhost:11434

# Model to use (default: translategemma:latest)
MYGLOT_OLLAMA_MODEL=translategemma:latest

# TTS and STT still use Google (or fake for offline dev)
MYGLOT_TTS_PROVIDER=google
MYGLOT_STT_PROVIDER=google
```

Restart MyGlot:

```bash
# If running with task:
task dev

# Or with Docker:
task restart
```

---

## 5. Verify it works

### From the MyGlot UI

1. Open <http://localhost:8000>.
2. Go to **Settings** → click **Test Providers**. The translator should show `ollama: ok`.
3. On the **Home** tab, type a phrase (e.g. "Good morning") and click **Translate**.
4. You should see:
   - The translated text filled in.
   - A **Translation Breakdown** section below with a word-by-word explanation in a table or bullet list.

### From the command line (without MyGlot)

```bash
curl -s http://localhost:11434/api/generate \
  -d '{"model":"translategemma:latest","prompt":"Translate the following from English to German: Good morning","stream":false}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['response'])"
```

---

## 6. How the Ollama translation prompt works

MyGlot sends a structured prompt to the Ollama model that asks for:

1. **The translation** — extracted from between `---TRANSLATION_START---` / `---TRANSLATION_END---` markers.
2. **A word-by-word explanation** — extracted from between `---EXPLANATION_START---` / `---EXPLANATION_END---` markers, formatted as Markdown.

The prompt is defined in `backend/app/providers/ollama/translate.py` in the `_build_prompt()` function. You can edit it to change the style of explanation (e.g. prefer tables vs bullet lists, add pronunciation notes, etc.).

If you change the marker format, also update `_parse_response()` in the same file to match.

---

## 7. Troubleshooting

### "Ollama connection error ... Is the Ollama server running?"
- Make sure `ollama serve` is running (or the Ollama desktop app is open).
- Check the URL: `curl http://localhost:11434/` should return `Ollama is running`.
- If using Docker, Ollama runs on the **host** machine, not inside the container. Set `MYGLOT_OLLAMA_BASE_URL=http://host.docker.internal:11434` in `.env`.

### Translations are slow
- First request after starting Ollama is slow (model loading). Subsequent requests are faster.
- Larger models are slower. Try a smaller model like `translategemma:latest` or `gemma3:4b`.
- Make sure you have enough RAM. The model needs to fit in memory (check with `ollama ps`).

### Empty or garbled translations
- The model might not support the language pair well. Try a different model.
- Check `ollama ps` to confirm the model is loaded.
- Look at the raw Ollama response in the server logs for debugging.

### Translation works but no explanation appears
- Some models may not follow the structured prompt format consistently. The explanation is optional — if the model doesn't produce the `---EXPLANATION_START---` / `---EXPLANATION_END---` markers, the translation still works but no breakdown is shown.
- Try a more capable model (e.g. `gemma3:4b` or `mistral`) for better prompt-following.

---

## 8. Running with Docker

When running MyGlot in Docker, Ollama still runs on the host machine. The container needs to reach the host's `localhost:11434`.

In `.env`:
```dotenv
MYGLOT_OLLAMA_BASE_URL=http://host.docker.internal:11434
```

This works on Docker Desktop (macOS/Windows). On Linux, use:
```dotenv
MYGLOT_OLLAMA_BASE_URL=http://172.17.0.1:11434
```
Or run Docker with `--network host`.
