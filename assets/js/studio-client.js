/* =========================================================================
 * studio-client.js — transport layer for AI Studio.
 *
 * The studio in index.html currently answers from an in-page regex DB. This
 * module puts a real API in front of that DB while keeping the DB as the
 * availability floor: any failure — no key, rate limit, cold-start timeout,
 * offline visitor — falls back to the answer the page already knows.
 *
 * A recruiter must never see an error state. That is the whole design rule.
 *
 * Contract: ARCHITECTURE.md §6. Mirrors agent/schemas.py by hand — change both
 * in the same commit.
 *
 * Usage from the studio IIFE:
 *     const reply = await StudioClient.ask(question, historyArray);
 *     // reply: { answer_html, agent, intent, citations, trace, degraded }
 * ========================================================================= */

window.StudioClient = (function () {
  "use strict";

  var ENDPOINT = "/api/chat";
  var TIMEOUT_MS = 12000;   // beyond this the walk animation stops covering the wait
  var MAX_HISTORY = 6;

  /* One id per browser tab. Not a cookie, not stored, not PII — it exists only
     so the rate limiter and the trace log can group a session's turns. */
  var sessionId = (function () {
    try {
      return crypto.randomUUID();
    } catch (e) {
      return "s-" + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
    }
  })();

  /* The trace the offline path reports, so the stage choreography is identical
     whether the answer came from the API or from the in-page DB. */
  function localTrace(agent, needsChart) {
    var t = [
      { actor: "hana", act: "triage",   label: "Got it. Classifying the question..." },
      { actor: "vy",   act: "retrieve", label: "On it. Checking the research wall..." },
      { actor: "minh", act: "answer",   label: "Here is the full context." }
    ];
    if (needsChart) t.push({ actor: "kai", act: "chart", label: "Charting the numbers..." });
    return t;
  }

  /**
   * Ask the studio a question.
   * Always resolves — never rejects — so the caller has no error branch.
   *
   * @param {string} message
   * @param {Array<{role:string,content:string}>} history
   * @returns {Promise<Object>} ChatResponse-shaped object
   */
  async function ask(message, history) {
    var controller = new AbortController();
    var timer = setTimeout(function () { controller.abort(); }, TIMEOUT_MS);

    try {
      var res = await fetch(ENDPOINT, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          message: String(message).slice(0, 300),
          session_id: sessionId,
          history: (history || []).slice(-MAX_HISTORY)
        }),
        signal: controller.signal
      });

      if (!res.ok) throw new Error("http " + res.status);
      var data = await res.json();
      if (!data || !data.answer_html) throw new Error("empty answer");
      return data;
    } catch (err) {
      return offline(message, err);
    } finally {
      clearTimeout(timer);
    }
  }

  /**
   * Fallback tier: the offline DB that ships inside index.html.
   * `window.StudioFallback.lookup` is provided by studio-fallback.js (step 1 of
   * the migration in ARCHITECTURE.md §7). While that extraction has not
   * happened, this returns null and the caller keeps using its own DB.
   */
  function offline(message, err) {
    if (window.console && err) console.debug("[studio] degraded:", err.message);

    var fb = window.StudioFallback && window.StudioFallback.lookup;
    if (!fb) return null;

    var entry = fb(message);
    return {
      answer_html: entry.h,
      agent: entry.a,
      intent: entry.intent || "profile",
      citations: [],
      trace: localTrace(entry.a, !!entry.chart),
      degraded: true,
      latency_ms: 0
    };
  }

  /** Health probe — used by nothing in the UI, handy in the console. */
  async function health() {
    try {
      var r = await fetch("/api/health");
      return await r.json();
    } catch (e) {
      return { ok: false };
    }
  }

  return { ask: ask, health: health, sessionId: sessionId };
})();
