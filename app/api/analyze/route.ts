import { NextResponse } from "next/server";
import { GoogleGenerativeAI } from "@google/generative-ai";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    // Accept both { question } (from frontend) or { prompt }
    const question = body.question || body.prompt || "";
    const item = body.item || {};

    const prompt = `
Anda adalah asisten untuk analis Kominfo (Indonesia).
Jawab singkat dan profesional dalam Bahasa Indonesia.
Format jawaban menggunakan Markdown bila bermanfaat (heading ringkas, bullet list, kode).

Konteks Kasus:
- URL: ${item.link || "-"}
- Kategori Terdeteksi: ${item.jenis || "-"}
- Kepercayaan: ${item.kepedean ?? "-"}%
- Status: ${item.status || "-"}
- Penalaran Otomatis: ${item.reasoning || "-"}

Pertanyaan Pengguna:
${question}
`;

    // Validasi API key
    const apiKey = process.env.GOOGLE_API_KEY;

    if (!apiKey) {
      console.error("GOOGLE_API_KEY tidak ditemukan");
      return NextResponse.json({ error: "API key tidak dikonfigurasi" }, { status: 500 });
    }

    // Inisialisasi dengan API key
    const genAI = new GoogleGenerativeAI(apiKey);

    // Gunakan model yang bekerja: gemini-2.5-flash
    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

    // Generate content. SDK response shapes may vary so handle safely.
    const result = await model.generateContent(prompt as any);

    // Try a few ways to extract text from the SDK response
    let text = "";
    try {
      if (result?.response?.text) {
        // some SDKs expose a function
        text = typeof result.response.text === "function" ? result.response.text() : String(result.response.text);
      }
    } catch (e) {
      // ignore
    }

    if (!text) {
      // fallback: inspect candidates/content
      try {
        // @ts-ignore
        const data: any = result;
        text =
          data?.candidates?.[0]?.content?.[0]?.text ||
          data?.candidates?.[0]?.output ||
          data?.outputText ||
          data?.output?.[0]?.content?.[0]?.text ||
          "";
      } catch (e) {
        // ignore
      }
    }

    // clean whitespace and simple artifacts
    const cleaned = String(text || "")
      .replace(/\r\n/g, "\n")
      .replace(/[ \t]+\n/g, "\n")
      .replace(/\n{3,}/g, "\n\n")
      .trim()
      .replace(/^"|"$/g, "")

    if (!cleaned) {
      console.error("Gemini returned no text", JSON.stringify(result));
      // In development, return a helpful reply so the UI flow can be tested.
      if (process.env.NODE_ENV !== "production") {
        return NextResponse.json({ reply: "Model returned no text. Check server logs for details." });
      }
      return NextResponse.json({ error: "No text returned from model" }, { status: 500 });
    }

    // If we have cleaned text, return it
    if (cleaned) {
      return NextResponse.json({ reply: cleaned, modelUsed: "gemini-2.5-flash" });
    }

    // Fallback: try Vercel AI generateText using GEMINI_API_KEY if available
    try {
      const { generateText } = await import("ai")
      const genKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY || ""
      if (genKey) {
        const resp = await generateText({ model: "google/gemini-1.5-flash", prompt, apiKey: genKey } as any)
        const rt = String((resp as any)?.text || (resp as any)?.outputText || "")
          .replace(/\r\n/g, "\n")
          .replace(/[ \t]+\n/g, "\n")
          .replace(/\n{3,}/g, "\n\n")
          .trim()
          .replace(/^"|"$/g, "")

        if (rt) return NextResponse.json({ reply: rt, modelUsed: "generateText-fallback" })
      }
    } catch (e) {
      console.warn("generateText fallback failed:", e)
    }

    return NextResponse.json({ error: "No text returned from model" }, { status: 500 })
  } catch (error: any) {
    console.error("Error generating text:", error);
    return NextResponse.json(
      { error: error?.message || "Terjadi kesalahan", details: error?.errorDetails || null },
      { status: error?.status || 500 },
    );
  }
}