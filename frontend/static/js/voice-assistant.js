// Voice assistant widget: real speech-to-text via the browser's native
// SpeechRecognition API, real text-to-speech via SpeechSynthesis — no
// server-side audio processing, no fabricated "AI voice" beyond what the
// browser genuinely provides. Falls back to a text box on browsers that
// don't support SpeechRecognition (e.g. Firefox desktop) so the assistant
// still works everywhere, just without the mic.
//
// Include this script, then call initVoiceAssistant() once the DOM is ready.

function initVoiceAssistant() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const supportsSTT = !!SpeechRecognition;
  const supportsTTS = "speechSynthesis" in window;

  const widget = document.createElement("div");
  widget.id = "voice-assistant-widget";
  widget.className = "fixed bottom-5 right-5 z-50 flex flex-col items-end gap-2";
  widget.innerHTML = `
    <div id="va-panel" class="hidden w-80 max-w-[90vw] rounded-2xl bg-surface-container-lowest shadow-lg p-space-md flex flex-col gap-space-sm">
      <div class="flex items-center justify-between">
        <span class="font-headline-sm text-headline-sm">Ask OmniSure</span>
        <button id="va-close" class="font-label-sm text-label-sm text-on-surface-variant">✕</button>
      </div>
      <p id="va-status" class="font-body-sm text-body-sm text-on-surface-variant">
        ${supportsSTT ? "Tap the mic and speak, or type below." : "Speech recognition isn't supported in this browser — type your request below."}
      </p>
      <div id="va-response" class="hidden p-3 rounded-xl bg-surface-container font-body-sm text-body-sm"></div>
      <div class="flex gap-2">
        <input id="va-text-input" type="text" placeholder="e.g. file a claim for my car"
          class="flex-1 px-3 py-2 rounded-xl bg-surface-container-low border border-outline-variant font-body-sm text-body-sm"/>
        ${supportsSTT ? '<button id="va-mic" class="w-10 h-10 rounded-full bg-secondary text-on-secondary flex items-center justify-center">🎤</button>' : ""}
        <button id="va-send" class="px-3 py-2 rounded-xl bg-secondary text-on-secondary font-label-sm text-label-sm font-semibold">Go</button>
      </div>
    </div>
    <button id="va-toggle" class="w-14 h-14 rounded-full bg-secondary text-on-secondary shadow-lg text-2xl flex items-center justify-center">🎙️</button>
  `;
  document.body.appendChild(widget);

  const panel = document.getElementById("va-panel");
  const toggle = document.getElementById("va-toggle");
  const closeBtn = document.getElementById("va-close");
  const statusEl = document.getElementById("va-status");
  const responseEl = document.getElementById("va-response");
  const textInput = document.getElementById("va-text-input");
  const sendBtn = document.getElementById("va-send");
  const micBtn = document.getElementById("va-mic");

  toggle.addEventListener("click", () => panel.classList.toggle("hidden"));
  closeBtn.addEventListener("click", () => panel.classList.add("hidden"));

  function speak(text) {
    if (!supportsTTS) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    window.speechSynthesis.speak(utterance);
  }

  async function handleRequest(text) {
    if (!text || !text.trim()) return;
    statusEl.textContent = "Thinking...";
    responseEl.classList.add("hidden");

    try {
      const result = await apiFetch("/assistant/interpret", {
        method: "POST",
        body: JSON.stringify({ text }),
      });

      responseEl.textContent = result.spoken_response;
      responseEl.classList.remove("hidden");
      statusEl.textContent = result.demo_mode
        ? "Understood via rule-based matching (no LLM key configured)."
        : "Understood.";
      speak(result.spoken_response);

      setTimeout(() => {
        if (result.action === "start_claim") {
          window.location.href = `/claims.html?policy_id=${result.policy_id}&type=${result.insurance_type_code}`;
        } else if (result.action === "explain_policy") {
          window.location.href = `/dashboard.html?explain=${result.policy_id}`;
        } else if (result.action === "view_claims") {
          window.location.href = "/claims.html";
        } else if (result.action === "open_advisor") {
          window.location.href = "/dashboard.html#advisor";
        }
        // "clarify" and "none" actions stay on the current page — the spoken/shown response is the full reply.
      }, 1400);
    } catch (err) {
      statusEl.textContent = err.message;
    }
  }

  sendBtn.addEventListener("click", () => {
    handleRequest(textInput.value);
    textInput.value = "";
  });
  textInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      handleRequest(textInput.value);
      textInput.value = "";
    }
  });

  if (supportsSTT) {
    const recognition = new SpeechRecognition();
    recognition.lang = "en-IN";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    let listening = false;
    micBtn.addEventListener("click", () => {
      if (listening) {
        recognition.stop();
        return;
      }
      panel.classList.remove("hidden");
      statusEl.textContent = "Listening...";
      micBtn.classList.add("animate-pulse");
      recognition.start();
    });

    recognition.addEventListener("start", () => {
      listening = true;
    });
    recognition.addEventListener("end", () => {
      listening = false;
      micBtn.classList.remove("animate-pulse");
    });
    recognition.addEventListener("result", (event) => {
      const transcript = event.results[0][0].transcript;
      textInput.value = transcript;
      handleRequest(transcript);
    });
    recognition.addEventListener("error", (event) => {
      statusEl.textContent = `Mic error: ${event.error}. You can type instead.`;
    });
  }
}
