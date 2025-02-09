import { NextRequest, NextResponse } from "next/server";
import OpenAI from "openai";
import axios from "axios"

// Instantiate the OpenAI client with the API key from process.env.
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(req: NextRequest) {
  try {
    // Parse the incoming form-data
    const formData = await req.formData();
    formData.append(
        "model",
        "whisper-1"
    )

    const {data} = await axios.post(
        "https://api.openai.com/v1/audio/transcriptions",
        formData,
        {
            headers: {
                Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
            },
        }
    )
    return NextResponse.json({ data });
  } catch (e: any) {
    return NextResponse.json(
      { error: e.message || "An unknown error occurred." },
      { status: e.status || 500 }
    );
  }
}
