const API = "http://localhost:8000";
const messages = document.querySelector("#messages");
const statusText = document.querySelector("#status");
let answerPending = false;
let syncPending = false;
let syncPollTimer;

async function sendRequest(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API}${path}`, options);
  } catch {
    throw new Error("Backend is unavailable. Start the API and try again.");
  }

  const result = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = result.detail;
    throw new Error(typeof detail === "string" ? detail : "The request failed. Please try again.");
  }
  return result;
}

function addMessage(text, role, sources = [], timings = null) {
  document.querySelector("#welcome").hidden = true;
  const item = document.createElement("div");
  item.className = `message ${role}`;
  item.textContent = text;

  if (sources.length) {
    const links = document.createElement("div");
    links.className = "sources";
    const seenEmails = new Set();
    for (const source of sources) {
      if (seenEmails.has(source.email_id)) continue;
      seenEmails.add(source.email_id);
      const link = document.createElement("a");
      link.href = source.gmail_link;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.textContent = source.subject || "Open email";
      link.title = source.subject || "Open email";
      links.append(link);
    }
    item.append(links);
  }

  if (timings) {
    const parts = [
      ["Search", timings.retrieval_time],
      ["Email context", timings.context_time],
      ["Ollama", timings.generation_time],
      ["Load", timings.model_load_time],
      ["Prompt", timings.prompt_eval_time],
      ["Generate", timings.token_gen_time],
      ["Total", timings.total_time]
    ].filter(([, seconds]) => Number.isFinite(seconds));

    if (parts.length) {
      const details = document.createElement("div");
      details.className = "timings";
      details.textContent = parts.map(([label, seconds]) => `${label} ${seconds.toFixed(2)}s`).join(" · ");
      if (Number.isFinite(timings.tokens_per_second)) {
        details.textContent += ` · ${timings.prompt_tokens} in / ${timings.output_tokens} out · ${timings.tokens_per_second} tok/s`;
      }
      item.append(details);
    }
  }

  messages.append(item);
  messages.scrollTop = messages.scrollHeight;
}

function addThinking() {
  document.querySelector("#welcome").hidden = true;
  const bubble = document.createElement("div");
  bubble.className = "message assistant thinking";

  const label = document.createElement("span");
  label.textContent = "Thinking";
  const dots = document.createElement("span");
  dots.className = "thinking-dots";
  dots.textContent = "···";
  bubble.append(label, dots);
  messages.append(bubble);
  messages.scrollTop = messages.scrollHeight;
  return bubble;
}

function showSyncProgress(progress) {
  const panel = document.querySelector("#sync-progress");
  const label = document.querySelector("#sync-progress-label");
  const count = document.querySelector("#sync-progress-count");
  const bar = document.querySelector("#sync-progress-bar");
  panel.hidden = false;

  if (progress.phase === "connecting") {
    label.textContent = "Connecting to Gmail and finding recent emails…";
    count.textContent = "Preparing";
    bar.style.width = "4%";
    return;
  }

  const total = progress.total || 0;
  const processed = progress.processed || 0;
  const remaining = Math.max(0, total - processed);
  label.textContent = total === 0
    ? "No emails found to sync."
    : `${processed} of ${total} processed · ${remaining} left`;
  count.textContent = `${progress.synced || 0} added · ${progress.skipped || 0} skipped${progress.failed ? ` · ${progress.failed} failed` : ""}`;
  bar.style.width = total === 0 ? "100%" : `${Math.round(processed / total * 100)}%`;
}

async function pollSyncProgress() {
  try {
    const progress = await sendRequest("/sync/status");
    if (progress.active || progress.phase === "complete" || progress.phase === "error") {
      showSyncProgress(progress);
    }
  } catch {
    // The sync request will show its own error if the API cannot be reached.
  }

  if (syncPending) {
    syncPollTimer = setTimeout(pollSyncProgress, 700);
  }
}

document.querySelector("#connect").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  button.disabled = true;
  statusText.textContent = "Waiting for Google sign-in…";
  try {
    const result = await sendRequest("/connect", { method: "POST" });
    button.textContent = "Gmail connected";
    button.title = result.email;
    document.querySelector("#connection-state").classList.add("connected");
    document.querySelector("#connection-label").textContent = result.email;
    statusText.textContent = "Gmail connected.";
  } catch (error) {
    statusText.textContent = error.message;
    button.disabled = false;
  }
});

document.querySelector("#sync").addEventListener("click", async (event) => {
  if (answerPending || syncPending) return;
  const button = event.currentTarget;
  const limitInput = document.querySelector("#limit");
  if (!limitInput.reportValidity()) return;

  syncPending = true;
  button.disabled = true;
  document.querySelector("#send").disabled = true;
  document.querySelector("#question").disabled = true;
  document.querySelector("#sync-progress").hidden = false;
  document.querySelector("#sync-progress-label").textContent = "Starting sync…";
  document.querySelector("#sync-progress-count").textContent = "";
  document.querySelector("#sync-progress-bar").style.width = "2%";
  statusText.textContent = "Syncing email…";
  pollSyncProgress();
  try {
    const result = await sendRequest("/sync", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ limit: Number(limitInput.value) })
    });
    const summary = `${result.synced} added · ${result.skipped} already synced`;
    document.querySelector("#sync-label").textContent = summary;
    const finalStatus = await sendRequest("/sync/status");
    showSyncProgress(finalStatus);
    statusText.textContent = result.failed
      ? `${summary}; ${result.failed} failed.`
      : `Sync complete: ${summary}.`;
  } catch (error) {
    document.querySelector("#sync-progress-label").textContent = "Sync failed";
    document.querySelector("#sync-progress-count").textContent = "";
    statusText.textContent = error.message;
  } finally {
    syncPending = false;
    clearTimeout(syncPollTimer);
    button.disabled = false;
    document.querySelector("#send").disabled = false;
    document.querySelector("#question").disabled = false;
  }
});

document.querySelector("#chat-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (answerPending || syncPending) return;

  const input = document.querySelector("#question");
  const question = input.value.trim();
  if (!question) return;

  answerPending = true;
  addMessage(question, "user");
  const thinking = addThinking();
  input.value = "";
  input.disabled = true;
  input.placeholder = "Waiting for your answer…";
  document.querySelector("#send").disabled = true;
  document.querySelector("#sync").disabled = true;
  document.querySelector("#chat-form").setAttribute("aria-busy", "true");
  statusText.textContent = "Thinking…";
  try {
    const result = await sendRequest("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question })
    });
    thinking.remove();

    if (result.status === "llm_error") {
      addMessage("Ollama could not answer. Check that it is running and the model is installed.", "assistant", [], result);
      statusText.textContent = "Ollama request failed.";
      return;
    }
    if (result.status === "invalid_response") {
      addMessage(result.error || "The model returned an invalid answer. Please try again.", "assistant", [], result);
      statusText.textContent = "The answer could not be processed.";
      return;
    }

    addMessage(result.answer || "I couldn't answer that from your email.", "assistant", result.sources || [], result);
    statusText.textContent = result.status === "insufficient_evidence"
      ? "No matching email evidence was found."
      : "Your email stays on your device.";
  } catch (error) {
    thinking.remove();
    addMessage(error.message, "assistant");
    statusText.textContent = error.message;
  } finally {
    thinking.remove();
    answerPending = false;
    input.disabled = false;
    input.placeholder = "Ask anything about your email…";
    document.querySelector("#send").disabled = false;
    document.querySelector("#sync").disabled = false;
    document.querySelector("#chat-form").removeAttribute("aria-busy");
    input.focus();
  }
});

document.querySelectorAll(".suggestion").forEach((button) => {
  button.addEventListener("click", () => {
    if (answerPending || syncPending) return;
    const input = document.querySelector("#question");
    input.value = button.textContent;
    input.focus();
  });
});

sendRequest("/health")
  .then(() => {
    statusText.textContent = "Your email stays on your device.";
  })
  .catch((error) => {
    statusText.textContent = error.message;
  });
