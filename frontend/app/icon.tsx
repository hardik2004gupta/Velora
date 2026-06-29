import { ImageResponse } from "next/og";

export const size = { width: 32, height: 32 };
export const contentType = "image/png";

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: 32,
          height: 32,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          borderRadius: 7.5,
          background: "linear-gradient(135deg, #6366f1 0%, #7c3aed 100%)",
        }}
      >
        <svg width="22" height="22" viewBox="0 0 28 28" fill="none">
          {/* Left input extension */}
          <line x1="4.5" y1="10" x2="8" y2="10" stroke="rgba(255,255,255,0.45)" strokeWidth="1.25" strokeLinecap="round" />
          {/* Right input extension */}
          <line x1="20" y1="10" x2="23.5" y2="10" stroke="rgba(255,255,255,0.45)" strokeWidth="1.25" strokeLinecap="round" />
          {/* Left V arm */}
          <line x1="8" y1="10" x2="14" y2="19" stroke="white" strokeWidth="1.75" strokeLinecap="round" />
          {/* Right V arm */}
          <line x1="20" y1="10" x2="14" y2="19" stroke="white" strokeWidth="1.75" strokeLinecap="round" />
          {/* Left node */}
          <circle cx="8" cy="10" r="2" fill="white" />
          {/* Right node */}
          <circle cx="20" cy="10" r="2" fill="white" />
          {/* Output node */}
          <circle cx="14" cy="19" r="2.5" fill="white" />
        </svg>
      </div>
    ),
    { ...size }
  );
}
