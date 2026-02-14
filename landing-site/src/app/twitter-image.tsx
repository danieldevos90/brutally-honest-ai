import { ImageResponse } from "next/og";

export const runtime = "edge";

export const alt = "Brutally Honest";
export const size = {
  width: 1200,
  height: 600,
};

export default function TwitterImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: 64,
          background: "#0a0a0a",
          color: "#ffffff",
        }}
      >
        <div style={{ fontSize: 44, fontWeight: 700, letterSpacing: -1 }}>
          Brutally Honest
        </div>
        <div style={{ marginTop: 18, fontSize: 26, color: "#a0a0a0", maxWidth: 900 }}>
          Truth in every conversation.
        </div>
      </div>
    ),
    size
  );
}

