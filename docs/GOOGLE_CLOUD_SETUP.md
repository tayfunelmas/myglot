# Google Cloud Setup Guide for MyGlot

This guide walks you through everything you need on the **Google Cloud** side so MyGlot can use Google Translate, Text-to-Speech (TTS), and Speech-to-Text (STT). You only need to do this once.

> **Time:** ~10–15 minutes.
> **Cost:** all three APIs have generous free monthly tiers. You must still enable **billing** on the project — Google will not charge you unless you exceed the free tier.

---

## 0. What you'll end up with

- A Google Cloud **project** (new or existing).
- Three APIs **enabled** in that project: Translation, Text-to-Speech, Speech-to-Text.
- A **service account** with just enough permission to call those APIs.
- A **JSON key file** saved locally at `./secrets/gcp.json`.
- A `.env` entry: `GOOGLE_APPLICATION_CREDENTIALS=./secrets/gcp.json`.

---

## 1. Prerequisites

- A Google account (gmail or Workspace).
- A credit/debit card to enable billing. New Google Cloud users also get a free trial credit.
- A terminal. The guide shows both **Console (web UI)** and **`gcloud` CLI** paths — pick whichever you prefer. The CLI path is faster once installed.

Install the CLI (optional, recommended):
- macOS: `brew install --cask google-cloud-sdk`
- Other: <https://cloud.google.com/sdk/docs/install>

Then sign in:
```bash
gcloud auth login
```

---

## 2. Create (or pick) a Google Cloud project

### Option A — Web Console
1. Go to <https://console.cloud.google.com/projectcreate>.
2. **Project name:** `myglot` (anything is fine).
3. **Project ID:** will be auto-generated (e.g. `myglot-472913`). Copy it — you'll need it.
4. Click **Create** and wait a few seconds, then select the project in the top bar.

### Option B — CLI
```bash
# pick a globally-unique id; lowercase, digits, hyphens
export PROJECT_ID="myglot-$(date +%s)"
gcloud projects create "$PROJECT_ID" --name="MyGlot"
gcloud config set project "$PROJECT_ID"
```

Verify:
```bash
gcloud config get-value project
```

---

## 3. Enable billing on the project

All three APIs require a project with billing linked, even while you stay within the free tier.

### Web Console
1. Go to <https://console.cloud.google.com/billing>.
2. If you don't have a billing account yet, click **Create account** and follow the steps (adds a payment method).
3. Open <https://console.cloud.google.com/billing/linkedaccount>, select your project, and **Link a billing account**.

### CLI
```bash
# list your billing accounts
gcloud billing accounts list
# link one (use the ACCOUNT_ID from the list, format: 0X0X0X-0X0X0X-0X0X0X)
gcloud billing projects link "$PROJECT_ID" --billing-account=ACCOUNT_ID
```

> **Free-tier note (approximate, check current docs for exact numbers):**
> - **Translation:** 500,000 characters / month free.
> - **Text-to-Speech:** 1M standard chars or 1M WaveNet/Neural2 chars / month free (separate buckets).
> - **Speech-to-Text:** 60 minutes / month free.
> Personal daily use is almost always within these limits.

---

## 4. Enable the three APIs

### Web Console
Open each link, make sure your project is selected in the top bar, and click **Enable**:
- Translation: <https://console.cloud.google.com/apis/library/translate.googleapis.com>
- Text-to-Speech: <https://console.cloud.google.com/apis/library/texttospeech.googleapis.com>
- Speech-to-Text: <https://console.cloud.google.com/apis/library/speech.googleapis.com>

### CLI
```bash
gcloud services enable \
  translate.googleapis.com \
  texttospeech.googleapis.com \
  speech.googleapis.com
```

Verify:
```bash
gcloud services list --enabled \
  --filter="config.name:(translate.googleapis.com OR texttospeech.googleapis.com OR speech.googleapis.com)"
```

You should see all three listed.

---

## 5. Create a service account

A **service account** is a non-human identity the app uses to call Google APIs. We'll give it only the roles it needs.

### Web Console
1. Go to <https://console.cloud.google.com/iam-admin/serviceaccounts>.
2. Click **Create service account**.
3. **Name:** `myglot-app`. **ID:** auto-filled. Click **Create and continue**.
4. **Grant roles** — add these two:
   - `Cloud Translation API User` (role id: `roles/cloudtranslate.user`)
   - `Cloud Speech Client` (role id: `roles/speech.client`) — this single role covers both TTS and STT.
5. Click **Continue**, then **Done** (skip the "grant users access" step).

### CLI
```bash
export SA_NAME="myglot-app"
export SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud iam service-accounts create "$SA_NAME" \
  --display-name="MyGlot app"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/cloudtranslate.user"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/speech.client"
```

> **Why these roles?** They're the least-privilege set for Translate + TTS + STT. Avoid broad roles like `Editor` or `Owner` for an app key.

---

## 6. Create and download a JSON key

> **Security:** this file is a **password-equivalent credential**. Never commit it, never paste it into chat/tickets/PRs, never put it in client-side code.

### Web Console
1. In <https://console.cloud.google.com/iam-admin/serviceaccounts>, click the `myglot-app` row.
2. Go to the **Keys** tab → **Add key** → **Create new key** → **JSON** → **Create**.
3. A file like `myglot-472913-abc123.json` downloads to your computer.
4. Move it into the project at `./secrets/gcp.json`:
   ```bash
   mkdir -p secrets
   mv ~/Downloads/myglot-*.json ./secrets/gcp.json
   chmod 600 ./secrets/gcp.json
   ```

### CLI
From the project root of MyGlot:
```bash
mkdir -p secrets
gcloud iam service-accounts keys create ./secrets/gcp.json \
  --iam-account="$SA_EMAIL"
chmod 600 ./secrets/gcp.json
```

Make sure `secrets/` is gitignored (MyGlot's `.gitignore` already covers this; double-check with `git check-ignore -v secrets/gcp.json`).

---

## 7. Wire the credentials into MyGlot

Edit `.env` in the project root (copy from `.env.example` if it doesn't exist yet):

```dotenv
GOOGLE_APPLICATION_CREDENTIALS=./secrets/gcp.json

# Make sure the Google providers are selected (these are the defaults):
MYGLOT_TRANSLATE_PROVIDER=google
MYGLOT_TTS_PROVIDER=google
MYGLOT_STT_PROVIDER=google
```

Restart the server (`Ctrl-C` and re-run `uvicorn`). In the MyGlot **Settings** page, click **Test Google connection** — you should see all three capabilities green.

---

## 8. Verify it works (without running MyGlot)

These optional one-liners confirm the key and APIs work before you even start the app. Run them from the project root.

```bash
# 1) Translate
GOOGLE_APPLICATION_CREDENTIALS=./secrets/gcp.json \
python - <<'PY'
from google.cloud import translate_v2 as translate
c = translate.Client()
print(c.translate("Good morning", source_language="en", target_language="de")["translatedText"])
PY
```
Expected output: `Guten Morgen`.

```bash
# 2) Text-to-Speech (writes hello.mp3)
GOOGLE_APPLICATION_CREDENTIALS=./secrets/gcp.json \
python - <<'PY'
from google.cloud import texttospeech as tts
c = tts.TextToSpeechClient()
resp = c.synthesize_speech(
    input=tts.SynthesisInput(text="Guten Morgen"),
    voice=tts.VoiceSelectionParams(language_code="de-DE"),
    audio_config=tts.AudioConfig(audio_encoding=tts.AudioEncoding.MP3),
)
open("hello.mp3","wb").write(resp.audio_content)
print("wrote hello.mp3", len(resp.audio_content), "bytes")
PY
```

```bash
# 3) Speech-to-Text (uses hello.mp3 from step 2; MP3 needs the v1p1beta1 client or LINEAR16;
#    for a quick check just list recognizers instead)
GOOGLE_APPLICATION_CREDENTIALS=./secrets/gcp.json \
python - <<'PY'
from google.cloud import speech
c = speech.SpeechClient()
# A lightweight no-op call: if auth/API is wrong, this raises.
print("SpeechClient initialized OK:", c.transport.host)
PY
```

If any of these fail with `403`, the API isn't enabled or the service account is missing the role. If they fail with `401` or `invalid_grant`, the key file path is wrong.

---

## 9. Rotating or revoking the key

**Rotate** (recommended every ~90 days or if you suspect leakage):
```bash
# create a new key
gcloud iam service-accounts keys create ./secrets/gcp.json.new \
  --iam-account="$SA_EMAIL"

# swap files
mv ./secrets/gcp.json.new ./secrets/gcp.json

# list old keys and delete them (keep only the current one)
gcloud iam service-accounts keys list --iam-account="$SA_EMAIL"
gcloud iam service-accounts keys delete KEY_ID --iam-account="$SA_EMAIL"
```

**Revoke everything** (e.g., leaked key):
```bash
# delete all keys for the SA
for k in $(gcloud iam service-accounts keys list --iam-account="$SA_EMAIL" \
           --managed-by=user --format='value(name.basename())'); do
  gcloud iam service-accounts keys delete "$k" --iam-account="$SA_EMAIL" --quiet
done
# or nuke the SA entirely
gcloud iam service-accounts delete "$SA_EMAIL"
```

Then restart MyGlot with a new key.

---

## 10. Monitoring usage & avoiding surprises

- **Billing dashboard:** <https://console.cloud.google.com/billing> → your account → **Reports**.
- **Budgets & alerts:** create a small budget (e.g., $5/month) with email alerts at 50/90/100%:
  <https://console.cloud.google.com/billing/budgets>.
- **API quotas/usage per API:** <https://console.cloud.google.com/apis/dashboard>.

---

## 11. Troubleshooting

| Symptom | Likely cause | Fix |
|--------|--------------|-----|
| `google.auth.exceptions.DefaultCredentialsError` | `GOOGLE_APPLICATION_CREDENTIALS` not set or path wrong | Check `.env`; path is relative to where you run `uvicorn`. Use an absolute path if unsure. |
| `403 ... API has not been used in project ... or it is disabled` | That specific API isn't enabled | Re-run §4 for the missing API. |
| `403 ... Permission 'cloudtranslate.generalModels.predict' denied` | Service account missing role | Re-run §5 role bindings. |
| `PERMISSION_DENIED: billing account ... is disabled` | Billing not linked or disabled | §3 — link an active billing account. |
| MP3 STT fails with `invalid encoding` | Google STT wants LINEAR16/FLAC/OPUS; MP3 from browser isn't accepted directly | MyGlot records as `audio/webm;codecs=opus`, which STT accepts. Only an issue if you hand-feed MP3. |
| Voices dropdown empty in Settings | TTS not enabled or wrong target lang code | Enable TTS; use BCP-47 like `de-DE`, not `de`. |
| Everything works locally but fails on a server | Key file not copied to the server or wrong path in that environment | Copy `secrets/gcp.json` there, or set `GOOGLE_APPLICATION_CREDENTIALS` to an absolute path on that host. |

---

## 12. Quick reference (copy-paste)

```bash
# one-time full setup via CLI
export PROJECT_ID="myglot-$(date +%s)"
gcloud projects create "$PROJECT_ID" --name="MyGlot"
gcloud config set project "$PROJECT_ID"

gcloud billing accounts list
gcloud billing projects link "$PROJECT_ID" --billing-account=REPLACE_WITH_ACCOUNT_ID

gcloud services enable \
  translate.googleapis.com \
  texttospeech.googleapis.com \
  speech.googleapis.com

export SA_NAME="myglot-app"
export SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
gcloud iam service-accounts create "$SA_NAME" --display-name="MyGlot app"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" --role="roles/cloudtranslate.user"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" --role="roles/speech.client"

mkdir -p secrets
gcloud iam service-accounts keys create ./secrets/gcp.json --iam-account="$SA_EMAIL"
chmod 600 ./secrets/gcp.json

echo "GOOGLE_APPLICATION_CREDENTIALS=./secrets/gcp.json" >> .env
```

Done. Start MyGlot and click **Test Google connection** in Settings.
