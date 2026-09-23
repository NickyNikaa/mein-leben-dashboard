// Kleiner Sync-Endpoint für die Einkaufsliste: speichert die Liste geräteübergreifend
// in Netlify Blobs, damit sie auf Handy und Mac gleich aussieht.
import { getStore } from "@netlify/blobs";

const KEY = "shopping";

export default async (req) => {
  const store = getStore("mein-leben-dashboard");

  if (req.method === "GET") {
    const data = await store.get(KEY, { type: "json" });
    return new Response(JSON.stringify(data || []), {
      headers: { "content-type": "application/json", "cache-control": "no-store" }
    });
  }

  if (req.method === "POST") {
    let body;
    try {
      body = await req.json();
    } catch (e) {
      return new Response("Ungültiges JSON", { status: 400 });
    }
    if (!Array.isArray(body)) {
      return new Response("Erwarte ein Array", { status: 400 });
    }
    await store.setJSON(KEY, body);
    return new Response(JSON.stringify({ ok: true }), {
      headers: { "content-type": "application/json" }
    });
  }

  return new Response("Method not allowed", { status: 405 });
};

export const config = { path: "/api/shopping" };
