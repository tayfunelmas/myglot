export class Recorder {
  constructor() {
    this._mediaRecorder = null;
    this._chunks = [];
    this._stream = null;
  }

  async start() {
    this._chunks = [];
    this._stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this._mediaRecorder = new MediaRecorder(this._stream, {
      mimeType: MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm",
    });
    this._mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) this._chunks.push(e.data);
    };
    this._mediaRecorder.start();
  }

  stop() {
    return new Promise((resolve) => {
      this._mediaRecorder.onstop = () => {
        const blob = new Blob(this._chunks, { type: this._mediaRecorder.mimeType });
        // Stop all tracks to release mic
        this._stream.getTracks().forEach((t) => {
          t.stop();
        });
        resolve(blob);
      };
      this._mediaRecorder.stop();
    });
  }

  get recording() {
    return this._mediaRecorder?.state === "recording";
  }
}
