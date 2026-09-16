/* Dashboard 2.0 — foundation
 * Versioned state + migration + safe task/challenge primitives.
 * This module is intentionally framework-free so it can be adopted incrementally.
 */
(function (global) {
  "use strict";

  var STORAGE_KEY = "meinlebenDashboard_v2";
  var VERSION = 2;

  function now() { return new Date().toISOString(); }
  function uid(prefix) {
    return (prefix || "id") + "_" + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  }

  function defaults() {
    return {
      version: VERSION,
      migratedAt: now(),
      tasks: [],
      habits: [],
      routines: [],
      goals: [],
      challenges: [],
      reflections: [],
      calendar: { custom: [], overrides: {}, skips: [] },
      lists: { shopping: [], wishlist: [] },
      insights: { distractions: [], timewasters: [] },
      emergency: []
    };
  }

  function migrateV1(v1) {
    var v2 = defaults();
    Object.keys(v2).forEach(function (key) {
      if (key === "version" || key === "migratedAt") return;
      if (v1 && v1[key] !== undefined) v2[key] = v1[key];
    });

    // Normalize the old task shape without destroying existing fields.
    v2.tasks = (v2.tasks || []).map(function (t) {
      return Object.assign({
        id: uid("task"), status: t.done ? "done" : "inbox", priority: 2,
        duration: 30, createdAt: t.added || now(), updatedAt: now()
      }, t, { id: t.id || uid("task") });
    });

    v2.habits = (v2.habits || []).map(function (h) {
      return Object.assign({ id: uid("habit"), history: h.hist || [], createdAt: now(), updatedAt: now() }, h, {
        id: h.id || uid("habit")
      });
    });

    v2.routines = (v2.routines || []).map(function (r) {
      return Object.assign({ id: uid("routine"), createdAt: now(), updatedAt: now() }, r, {
        id: r.id || uid("routine")
      });
    });

    return v2;
  }

  function load() {
    var raw = null;
    try { raw = JSON.parse(localStorage.getItem(STORAGE_KEY)); } catch (_) {}
    if (raw && raw.version === VERSION) return raw;

    // Existing production dashboard used this key. Migration is deliberately
    // read-only: the old data stays intact until the new state is verified.
    var old = null;
    try { old = JSON.parse(localStorage.getItem("meinlebenDashboard_v1")); } catch (_) {}
    if (old) return migrateV1(old);
    return defaults();
  }

  function save(state) {
    state.version = VERSION;
    state.updatedAt = now();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    return state;
  }

  function addTask(state, input) {
    var task = Object.assign({
      id: uid("task"), title: "", status: "inbox", priority: 2, duration: 30,
      area: "aufgaben", createdAt: now(), updatedAt: now()
    }, input || {});
    if (!task.title.trim()) throw new Error("Task title required");
    state.tasks.push(task);
    return task;
  }

  function completeTask(state, id) {
    var task = (state.tasks || []).find(function (t) { return t.id === id; });
    if (!task) return null;
    task.status = "done";
    task.done = true;
    task.completedAt = now();
    task.updatedAt = now();
    return task;
  }

  function completeChallengeToday(state, challengeId, dateKey) {
    var challenge = (state.challenges || []).find(function (c) { return c.id === challengeId; });
    if (!challenge) return false;
    challenge.history = challenge.history || {};
    if (challenge.history[dateKey]) return false; // prevents counter inflation / double completion
    challenge.history[dateKey] = now();
    challenge.updatedAt = now();
    return true;
  }

  global.DashboardV2 = {
    VERSION: VERSION,
    STORAGE_KEY: STORAGE_KEY,
    defaults: defaults,
    load: load,
    save: save,
    migrateV1: migrateV1,
    addTask: addTask,
    completeTask: completeTask,
    completeChallengeToday: completeChallengeToday
  };
})(window);
