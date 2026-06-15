"use client";

import { useState } from "react";
import { useI18n } from "@/components/providers";

/* ─── locale-aware inline text helper ─── */
function c(locale: string, en: React.ReactNode, ru: React.ReactNode): React.ReactNode {
  return locale === "ru" ? ru : en;
}

/* ══════════════════════════════════════════
   SVG Illustrations
══════════════════════════════════════════ */

function IllustrationGate() {
  return (
    <svg viewBox="0 0 140 108" fill="none" xmlns="http://www.w3.org/2000/svg"
         style={{ width: 130, height: 95, flexShrink: 0, opacity: 0.9 }}>
      {/* Stars */}
      <circle cx="18" cy="10" r="1.4" fill="#60A5FA" opacity=".7"/>
      <circle cx="60" cy="5"  r="1"   fill="#94A3B8" opacity=".5"/>
      <circle cx="108" cy="8" r="1.4" fill="#60A5FA" opacity=".6"/>
      <circle cx="130" cy="3" r="1"   fill="#38BDF8" opacity=".5"/>
      <circle cx="14" cy="32" r=".9"  fill="#A855F7" opacity=".4"/>
      {/* Left tower */}
      <rect x="4" y="24" width="50" height="76" fill="#0F1826" stroke="#2E3B5A" strokeWidth="1.5"/>
      {/* Right tower */}
      <rect x="86" y="24" width="50" height="76" fill="#0F1826" stroke="#2E3B5A" strokeWidth="1.5"/>
      {/* Battlements left */}
      {[4,17,30,43].map(x => (
        <rect key={x} x={x} y="16" width="9" height="10" fill="#1A2235" stroke="#2E3B5A" strokeWidth="1" rx="1"/>
      ))}
      {/* Battlements right */}
      {[86,99,112,125].map(x => (
        <rect key={x} x={x} y="16" width="9" height="10" fill="#1A2235" stroke="#2E3B5A" strokeWidth="1" rx="1"/>
      ))}
      {/* Arrow-slits */}
      {[16,36].map(x => (
        <rect key={x} x={x} y="48" width="5" height="18" rx="2.5" fill="rgba(96,165,250,0.14)" stroke="#2E3B5A" strokeWidth="1"/>
      ))}
      {[99,119].map(x => (
        <rect key={x} x={x} y="48" width="5" height="18" rx="2.5" fill="rgba(96,165,250,0.14)" stroke="#2E3B5A" strokeWidth="1"/>
      ))}
      {/* Gate arch fill */}
      <path d="M56 100 L56 54 Q70 28 84 54 L84 100" fill="rgba(59,130,246,0.18)" stroke="#3B82F6" strokeWidth="1.5"/>
      {/* Light rays from gate */}
      <line x1="70" y1="98" x2="48" y2="110" stroke="rgba(96,165,250,0.22)" strokeWidth="1.2"/>
      <line x1="70" y1="98" x2="92" y2="110" stroke="rgba(96,165,250,0.22)" strokeWidth="1.2"/>
      <line x1="70" y1="95" x2="70" y2="110" stroke="rgba(96,165,250,0.18)" strokeWidth="1"/>
      {/* Portcullis bars */}
      {[60,65,70,75,80].map(x => (
        <line key={x} x1={x} y1="55" x2={x} y2="100" stroke="rgba(46,59,90,0.7)" strokeWidth="1"/>
      ))}
      <line x1="57" y1="70" x2="83" y2="70" stroke="rgba(46,59,90,0.7)" strokeWidth="1"/>
      <line x1="57" y1="82" x2="83" y2="82" stroke="rgba(46,59,90,0.7)" strokeWidth="1"/>
    </svg>
  );
}

function IllustrationHourglass() {
  return (
    <svg viewBox="0 0 100 108" fill="none" xmlns="http://www.w3.org/2000/svg"
         style={{ width: 88, height: 95, flexShrink: 0, opacity: 0.9 }}>
      {/* Frame bars */}
      <line x1="22" y1="8"  x2="78" y2="8"  stroke="#4B6AA3" strokeWidth="3" strokeLinecap="round"/>
      <line x1="22" y1="100" x2="78" y2="100" stroke="#4B6AA3" strokeWidth="3" strokeLinecap="round"/>
      <line x1="25" y1="8" x2="25" y2="100" stroke="#374E74" strokeWidth="1.8"/>
      <line x1="75" y1="8" x2="75" y2="100" stroke="#374E74" strokeWidth="1.8"/>
      {/* Top glass */}
      <path d="M26 10 L74 10 L50 54 Z" fill="rgba(245,158,11,0.08)" stroke="#4B6AA3" strokeWidth=".8"/>
      {/* Sand top (partially filled) */}
      <path d="M26 10 L74 10 L66 32 L34 32 Z" fill="rgba(245,158,11,0.38)"/>
      {/* Bottom glass */}
      <path d="M26 98 L74 98 L50 54 Z" fill="rgba(245,158,11,0.07)" stroke="#4B6AA3" strokeWidth=".8"/>
      {/* Sand pile bottom */}
      <path d="M33 94 Q50 82 67 94 L67 98 L33 98 Z" fill="rgba(245,158,11,0.45)"/>
      {/* Falling grains */}
      <circle cx="49.5" cy="59" r="1.5" fill="#F59E0B" opacity=".9"/>
      <circle cx="50.5" cy="67" r="1.1" fill="#F59E0B" opacity=".7"/>
      <circle cx="50"   cy="74" r="1.3" fill="#F59E0B" opacity=".6"/>
      {/* Rune marks */}
      <text x="10" y="36" fontSize="11" fill="#60A5FA" opacity=".4" fontFamily="serif">⌬</text>
      <text x="78" y="70" fontSize="11" fill="#60A5FA" opacity=".35" fontFamily="serif">◊</text>
      {/* Neck glow */}
      <circle cx="50" cy="54" r="4" fill="rgba(96,165,250,0.18)"/>
    </svg>
  );
}

function IllustrationEquipment() {
  return (
    <svg viewBox="0 0 128 108" fill="none" xmlns="http://www.w3.org/2000/svg"
         style={{ width: 116, height: 95, flexShrink: 0, opacity: 0.9 }}>
      {/* Sword blade */}
      <path d="M28 96 L86 16" stroke="#60A5FA" strokeWidth="3.5" strokeLinecap="round"/>
      <path d="M30 93 L88 14" stroke="rgba(248,250,252,0.25)" strokeWidth="1" strokeLinecap="round"/>
      {/* Crossguard */}
      <rect x="20" y="74" width="34" height="6" rx="3" fill="#2A375A" stroke="#60A5FA" strokeWidth="1.2"/>
      {/* Pommel */}
      <circle cx="24" cy="99" r="7" fill="#1A2235" stroke="#4B6AA3" strokeWidth="1.8"/>
      <circle cx="24" cy="99" r="3.5" fill="#2A375A"/>
      {/* Grip */}
      <path d="M27 92 L36 78" stroke="#4B6AA3" strokeWidth="5" strokeLinecap="round"/>
      {/* Shield body */}
      <path d="M74 28 L100 28 L100 60 Q100 80 87 87 Q74 80 74 60 Z"
            fill="rgba(59,130,246,0.1)" stroke="#3B82F6" strokeWidth="2"/>
      {/* Shield center emblem */}
      <circle cx="87" cy="56" r="8" fill="rgba(59,130,246,0.18)" stroke="#60A5FA" strokeWidth="1"/>
      <path d="M87 48 L87 64 M79 56 L95 56" stroke="#60A5FA" strokeWidth="1.4" opacity=".5" strokeLinecap="round"/>
      {/* Shield stripe */}
      <path d="M74 44 L100 44" stroke="#2E3B5A" strokeWidth="1"/>
      {/* Blade tip glow */}
      <circle cx="87" cy="15" r="5" fill="rgba(96,165,250,0.2)"/>
      {/* Sparkle */}
      <circle cx="12" cy="22" r="2"   fill="#F59E0B" opacity=".7"/>
      <line x1="9"  y1="22" x2="15" y2="22" stroke="#F59E0B" strokeWidth="1" opacity=".5"/>
      <line x1="12" y1="19" x2="12" y2="25" stroke="#F59E0B" strokeWidth="1" opacity=".5"/>
    </svg>
  );
}

function IllustrationGems() {
  const gems = [
    { x: 2,  y: 56, s: 13, fill: "rgba(148,163,184,0.25)", stroke: "#64748B",  glow: "rgba(148,163,184,0.08)" },
    { x: 18, y: 50, s: 15, fill: "rgba(34,197,94,0.25)",   stroke: "#22C55E",  glow: "rgba(34,197,94,0.1)" },
    { x: 36, y: 44, s: 17, fill: "rgba(56,189,248,0.25)",  stroke: "#38BDF8",  glow: "rgba(56,189,248,0.1)" },
    { x: 56, y: 37, s: 19, fill: "rgba(59,130,246,0.25)",  stroke: "#3B82F6",  glow: "rgba(59,130,246,0.12)" },
    { x: 78, y: 29, s: 22, fill: "rgba(168,85,247,0.25)",  stroke: "#A855F7",  glow: "rgba(168,85,247,0.14)" },
    { x: 22, y: 75, s: 24, fill: "rgba(245,158,11,0.25)",  stroke: "#F59E0B",  glow: "rgba(245,158,11,0.15)" },
    { x: 55, y: 68, s: 28, fill: "rgba(239,68,68,0.25)",   stroke: "#EF4444",  glow: "rgba(239,68,68,0.18)" },
    { x: 93, y: 58, s: 18, fill: "rgba(248,250,252,0.2)",  stroke: "#F8FAFC",  glow: "rgba(248,250,252,0.12)" },
  ];
  return (
    <svg viewBox="0 0 124 106" fill="none" xmlns="http://www.w3.org/2000/svg"
         style={{ width: 110, height: 95, flexShrink: 0, opacity: 0.9 }}>
      {gems.map((g, i) => {
        const cx = g.x + g.s / 2, cy = g.y + g.s * 0.55;
        const pts = [
          [cx,     g.y].join(","),
          [g.x + g.s, g.y + g.s * 0.35].join(","),
          [g.x + g.s, g.y + g.s * 0.65].join(","),
          [cx,     g.y + g.s].join(","),
          [g.x,       g.y + g.s * 0.65].join(","),
          [g.x,       g.y + g.s * 0.35].join(","),
        ].join(" ");
        return (
          <g key={i}>
            <circle cx={cx} cy={cy} r={g.s * 0.75} fill={g.glow}/>
            <polygon points={pts} fill={g.fill} stroke={g.stroke} strokeWidth="1.2"/>
            <polygon
              points={`${cx},${g.y + 2} ${cx + g.s * 0.25},${g.y + g.s * 0.33} ${cx},${g.y + g.s * 0.38} ${cx - g.s * 0.25},${g.y + g.s * 0.33}`}
              fill={`${g.stroke}60`}
            />
          </g>
        );
      })}
    </svg>
  );
}

function IllustrationStats() {
  const bars = [
    { label: "ATK", pct: 0.75, color: "#3B82F6" },
    { label: "DEF", pct: 0.60, color: "#60A5FA" },
    { label: "HP",  pct: 0.85, color: "#EF4444" },
    { label: "CRT", pct: 0.45, color: "#F59E0B" },
    { label: "EVA", pct: 0.55, color: "#22C55E" },
  ];
  return (
    <svg viewBox="0 0 118 105" fill="none" xmlns="http://www.w3.org/2000/svg"
         style={{ width: 105, height: 95, flexShrink: 0, opacity: 0.9 }}>
      {bars.map(({ label, pct, color }, i) => {
        const y = 16 + i * 19;
        return (
          <g key={label}>
            <text x="2" y={y - 3} fontSize="7" fill="#64748B" fontFamily="monospace" letterSpacing="1">{label}</text>
            <rect x="2" y={y} width="114" height="8" rx="4" fill="#202B44"/>
            <rect x="2" y={y} width={114 * pct} height="8" rx="4" fill={color} opacity=".8"/>
            <rect x="2" y={y} width={114 * pct * 0.55} height="4" rx="2" fill={`${color}55`}/>
          </g>
        );
      })}
    </svg>
  );
}

function IllustrationCoins() {
  return (
    <svg viewBox="0 0 132 105" fill="none" xmlns="http://www.w3.org/2000/svg"
         style={{ width: 118, height: 95, flexShrink: 0, opacity: 0.9 }}>
      {/* Gold stack */}
      {[3,2,1,0].map(i => (
        <g key={i}>
          <rect x="8" y={70 - i * 9} width="42" height="9" fill="#C28F1A" stroke="#F59E0B" strokeWidth=".8"/>
          {i === 0 && <ellipse cx="29" cy={70 - i * 9} rx="21" ry="5.5" fill="#FBE08A" stroke="#F59E0B" strokeWidth=".8"/>}
        </g>
      ))}
      <ellipse cx="29" cy="34" rx="21" ry="5.5" fill="#C28F1A" stroke="#F59E0B" strokeWidth=".8"/>
      <text x="23" y="40" fontSize="11" fill="#7A5010" fontFamily="serif" fontWeight="bold">G</text>
      <text x="16" y="98" fontSize="7" fill="#F59E0B" fontFamily="monospace" letterSpacing=".5">GOLD</text>

      {/* Silver stack */}
      {[2,1,0].map(i => (
        <g key={i}>
          <rect x="56" y={72 - i * 9} width="34" height="9" fill="#A8B0C0" stroke="#CBD5E1" strokeWidth=".8"/>
          {i === 0 && <ellipse cx="73" cy={72 - i * 9} rx="17" ry="5" fill="#F5F7FB" stroke="#CBD5E1" strokeWidth=".8"/>}
        </g>
      ))}
      <ellipse cx="73" cy="45" rx="17" ry="5" fill="#A8B0C0" stroke="#CBD5E1" strokeWidth=".8"/>
      <text x="68" y="51" fontSize="10" fill="#6E7587" fontFamily="serif" fontWeight="bold">S</text>
      <text x="59" y="98" fontSize="7" fill="#CBD5E1" fontFamily="monospace" letterSpacing=".5">SILVER</text>

      {/* Copper */}
      {[1,0].map(i => (
        <g key={i}>
          <rect x="100" y={74 - i * 9} width="28" height="9" fill="#B66A2C" stroke="#F1A877" strokeWidth=".8"/>
          {i === 0 && <ellipse cx="114" cy={74 - i * 9} rx="14" ry="4.5" fill="#F1A877" stroke="#CD7C45" strokeWidth=".8"/>}
        </g>
      ))}
      <ellipse cx="114" cy="56" rx="14" ry="4.5" fill="#B66A2C" stroke="#F1A877" strokeWidth=".8"/>
      <text x="109" y="62" fontSize="9" fill="#4A2006" fontFamily="serif" fontWeight="bold">C</text>
      <text x="98" y="98" fontSize="7" fill="#F1A877" fontFamily="monospace" letterSpacing=".5">COPPER</text>

      {/* Sparkle */}
      <circle cx="8"  cy="22" r="2"   fill="#F59E0B" opacity=".65"/>
      <line x1="5"  y1="22" x2="11" y2="22" stroke="#F59E0B" strokeWidth=".9" opacity=".5"/>
      <line x1="8"  y1="19" x2="8"  y2="25" stroke="#F59E0B" strokeWidth=".9" opacity=".5"/>
    </svg>
  );
}

function IllustrationPotion() {
  return (
    <svg viewBox="0 0 120 108" fill="none" xmlns="http://www.w3.org/2000/svg"
         style={{ width: 104, height: 95, flexShrink: 0, opacity: 0.9 }}>
      {/* Big round flask */}
      <path d="M48 30 L48 50 Q24 64 24 84 Q24 100 48 100 L72 100 Q96 100 96 84 Q96 64 72 50 L72 30 Z"
            fill="rgba(20,184,166,0.10)" stroke="#2DD4BF" strokeWidth="2"/>
      {/* Liquid */}
      <path d="M30 72 Q60 64 90 72 Q92 100 72 100 L48 100 Q28 100 30 72 Z" fill="rgba(20,184,166,0.40)"/>
      {/* Bubbles */}
      <circle cx="52" cy="84" r="2.6" fill="rgba(167,243,208,0.8)"/>
      <circle cx="66" cy="90" r="2" fill="rgba(167,243,208,0.7)"/>
      <circle cx="60" cy="78" r="1.6" fill="rgba(167,243,208,0.6)"/>
      {/* Neck + cork */}
      <rect x="46" y="20" width="28" height="12" rx="2" fill="#1A2235" stroke="#2DD4BF" strokeWidth="1.6"/>
      <rect x="50" y="10" width="20" height="12" rx="3" fill="#3F2A1A" stroke="#A16207" strokeWidth="1.4"/>
      {/* Steam */}
      <path d="M56 8 Q52 2 58 -2" stroke="rgba(45,212,191,0.5)" strokeWidth="1.4" fill="none"/>
      <path d="M64 8 Q68 2 62 -2" stroke="rgba(45,212,191,0.4)" strokeWidth="1.4" fill="none"/>
      {/* Floating ingredient leaves */}
      <path d="M14 40 Q6 34 14 28 Q22 34 14 40 Z" fill="rgba(34,197,94,0.5)" stroke="#22C55E" strokeWidth="1"/>
      <path d="M104 46 Q112 40 104 34 Q96 40 104 46 Z" fill="rgba(34,197,94,0.45)" stroke="#22C55E" strokeWidth="1"/>
      {/* Sparkles */}
      <circle cx="18" cy="62" r="1.6" fill="#5EEAD4" opacity=".7"/>
      <circle cx="100" cy="68" r="1.4" fill="#5EEAD4" opacity=".6"/>
    </svg>
  );
}

function IllustrationShop() {
  return (
    <svg viewBox="0 0 132 108" fill="none" xmlns="http://www.w3.org/2000/svg"
         style={{ width: 116, height: 95, flexShrink: 0, opacity: 0.9 }}>
      {/* Stall awning */}
      <path d="M14 30 L118 30 L110 46 L22 46 Z" fill="rgba(192,132,252,0.16)" stroke="#C084FC" strokeWidth="1.6"/>
      {[14,29,44,59,74,89,104].map((x, i) => (
        <path key={x} d={`M${x} 30 L${x + 8} 46 L${x + 15} 30`} fill={i % 2 ? "rgba(192,132,252,0.28)" : "transparent"} stroke="#A855F7" strokeWidth=".8"/>
      ))}
      {/* Posts */}
      <rect x="20" y="46" width="3" height="40" fill="#374E74"/>
      <rect x="109" y="46" width="3" height="40" fill="#374E74"/>
      {/* Counter */}
      <rect x="16" y="84" width="100" height="10" rx="2" fill="#1A2235" stroke="#2E3B5A" strokeWidth="1.4"/>
      {/* Treasure chest */}
      <rect x="40" y="62" width="38" height="22" rx="2" fill="#3F2A1A" stroke="#A16207" strokeWidth="1.6"/>
      <path d="M40 62 Q59 48 78 62 Z" fill="rgba(245,158,11,0.25)" stroke="#F59E0B" strokeWidth="1.6"/>
      <rect x="55" y="66" width="8" height="9" rx="1.5" fill="#FBBF24" stroke="#A16207" strokeWidth="1"/>
      {/* Gem on counter */}
      <polygon points="92,66 99,70 96,80 88,80 85,70" fill="rgba(192,132,252,0.4)" stroke="#C084FC" strokeWidth="1.2"/>
      <polygon points="92,66 95,71 92,73 89,71" fill="#E9D5FF"/>
      {/* Sparkles */}
      <circle cx="59" cy="54" r="2" fill="#FBE08A" opacity=".8"/>
      <circle cx="104" cy="58" r="1.6" fill="#E9D5FF" opacity=".7"/>
    </svg>
  );
}

/* ══════════════════════════════════════════
   Section Components
══════════════════════════════════════════ */

function SectionHeading({
  id,
  illustration,
  accentColor,
  tag,
  title,
  subtitle,
}: {
  id: string;
  illustration: React.ReactNode;
  accentColor: string;
  tag: string;
  title: React.ReactNode;
  subtitle: React.ReactNode;
}) {
  return (
    <div
      id={id}
      style={{
        display: "flex", alignItems: "center", justifyContent: "space-between", gap: 20,
        padding: "22px 24px 18px",
        borderBottom: "1px solid #243150",
        borderTop: `3px solid ${accentColor}`,
        background: `linear-gradient(135deg, ${accentColor}10 0%, transparent 60%)`,
        borderRadius: "14px 14px 0 0",
      }}
    >
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
          fontSize: 10, letterSpacing: "0.22em", textTransform: "uppercase",
          color: accentColor, marginBottom: 6, opacity: 0.85,
        }}>{tag}</div>
        <h2 style={{
          fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
          fontSize: 22, fontWeight: 700, letterSpacing: "0.04em",
          color: "#F1F5F9", margin: 0, lineHeight: 1.2,
        }}>{title}</h2>
        <p style={{
          margin: "6px 0 0",
          fontSize: 13, color: "#94A3B8", lineHeight: 1.6,
        }}>{subtitle}</p>
      </div>
      <div style={{ flexShrink: 0, opacity: 0.9 }}>{illustration}</div>
    </div>
  );
}

function StepCard({
  num,
  color,
  title,
  body,
}: {
  num: number;
  color: string;
  title: React.ReactNode;
  body: React.ReactNode;
}) {
  return (
    <div style={{
      display: "flex", gap: 14, padding: "14px 16px",
      background: "#111827", border: "1px solid #2E3B5A",
      borderLeft: `3px solid ${color}`,
      borderRadius: 10,
    }}>
      <div style={{
        width: 28, height: 28, borderRadius: "50%", flexShrink: 0,
        background: `${color}22`, border: `1.5px solid ${color}`,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontFamily: "var(--font-mono)", fontSize: 11, fontWeight: 700, color,
        marginTop: 1,
      }}>{num}</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontSize: 13, fontWeight: 600, color: "#E5E7EB", marginBottom: 3,
        }}>{title}</div>
        <div style={{ fontSize: 12, color: "#94A3B8", lineHeight: 1.5 }}>{body}</div>
      </div>
    </div>
  );
}

function TipBox({ children, tone = "info" }: { children: React.ReactNode; tone?: "info" | "warn" | "good" }) {
  const palette = {
    info: { border: "rgba(59,130,246,0.35)", bg: "rgba(59,130,246,0.08)", icon: "💡", color: "#60A5FA" },
    warn: { border: "rgba(245,158,11,0.35)", bg: "rgba(245,158,11,0.08)", icon: "⚠", color: "#F59E0B" },
    good: { border: "rgba(34,197,94,0.35)",  bg: "rgba(34,197,94,0.08)",  icon: "✓", color: "#22C55E" },
  };
  const p = palette[tone];
  return (
    <div style={{
      display: "flex", gap: 10, padding: "10px 14px",
      background: p.bg, border: `1px solid ${p.border}`, borderRadius: 8,
    }}>
      <span style={{ fontSize: 13, flexShrink: 0, marginTop: 1, color: p.color }}>{p.icon}</span>
      <div style={{ fontSize: 12, color: "#94A3B8", lineHeight: 1.55 }}>{children}</div>
    </div>
  );
}

function InfoRow({ label, value, accent }: { label: React.ReactNode; value: React.ReactNode; accent?: string }) {
  return (
    <div style={{
      display: "flex", justifyContent: "space-between", alignItems: "center",
      gap: 12, padding: "7px 0", borderBottom: "1px dashed #243150",
    }}>
      <span style={{ fontSize: 12, color: "#94A3B8" }}>{label}</span>
      <span style={{
        fontFamily: "var(--font-mono)", fontSize: 12, fontWeight: 600,
        color: accent ?? "#E5E7EB",
      }}>{value}</span>
    </div>
  );
}

/* ── Rarity data ── */
const RARITIES = [
  { key: "f",  label: "F", nameEn: "Common",    nameRu: "Обычный",     color: "#94A3B8", border: "#475569", bg: "rgba(148,163,184,0.08)" },
  { key: "e",  label: "E", nameEn: "Uncommon",  nameRu: "Необычный",   color: "#22C55E", border: "rgba(34,197,94,0.5)",  bg: "rgba(34,197,94,0.09)" },
  { key: "d",  label: "D", nameEn: "Rare",      nameRu: "Редкий",      color: "#38BDF8", border: "rgba(56,189,248,0.5)", bg: "rgba(56,189,248,0.09)" },
  { key: "c",  label: "C", nameEn: "Epic",      nameRu: "Эпический",   color: "#3B82F6", border: "rgba(59,130,246,0.5)", bg: "rgba(59,130,246,0.09)" },
  { key: "b",  label: "B", nameEn: "Legendary", nameRu: "Легендарный", color: "#A855F7", border: "rgba(168,85,247,0.5)", bg: "rgba(168,85,247,0.09)" },
  { key: "a",  label: "A", nameEn: "Artifact",  nameRu: "Артефакт",    color: "#F59E0B", border: "rgba(245,158,11,0.5)", bg: "rgba(245,158,11,0.09)" },
  { key: "s",  label: "S", nameEn: "Ancient",   nameRu: "Древний",     color: "#EF4444", border: "rgba(239,68,68,0.5)",  bg: "rgba(239,68,68,0.09)" },
  { key: "ex", label: "EX",nameEn: "Exalted",   nameRu: "Превознесённый", color: "#F8FAFC", border: "rgba(248,250,252,0.5)", bg: "rgba(248,250,252,0.09)" },
];

const SLOT_ICONS: Record<string, string> = {
  Weapon: "⚔", Helmet: "⛨", Armor: "◫", Boots: "⌁", Ring: "⊙",
};
const SLOT_ICONS_RU: Record<string, string> = {
  "Оружие": "⚔", "Шлем": "⛨", "Броня": "◫", "Ботинки": "⌁", "Кольцо": "⊙",
};

/* ══════════════════════════════════════════
   Main Screen
══════════════════════════════════════════ */

type SectionId = "start" | "dungeons" | "equipment" | "rarity" | "stats" | "alchemy" | "shop" | "currency";

const SECTION_LIST: Array<{ id: SectionId; labelEn: string; labelRu: string; color: string }> = [
  { id: "start",     labelEn: "Getting Started", labelRu: "Начало",        color: "#60A5FA" },
  { id: "dungeons",  labelEn: "Dungeons",         labelRu: "Данжи",         color: "#A855F7" },
  { id: "equipment", labelEn: "Equipment",        labelRu: "Экипировка",    color: "#38BDF8" },
  { id: "rarity",    labelEn: "Rarity Tiers",     labelRu: "Редкость",      color: "#F59E0B" },
  { id: "stats",     labelEn: "Stats & Power",    labelRu: "Статы и Мощь",  color: "#22C55E" },
  { id: "alchemy",   labelEn: "Potions & Brewing",labelRu: "Зелья и варка", color: "#14B8A6" },
  { id: "shop",      labelEn: "Shop & Premium",   labelRu: "Магазин",       color: "#C084FC" },
  { id: "currency",  labelEn: "Currency",         labelRu: "Валюта",        color: "#FBBF24" },
];

export function GuidebookScreen() {
  const { locale } = useI18n();
  const [activeSection, setActiveSection] = useState<SectionId>("start");

  const scrollTo = (id: SectionId) => {
    setActiveSection(id);
    document.getElementById(`guide-${id}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="col animate-fade-in" style={{ gap: 0 }}>

      {/* ── Sticky section pill nav ── */}
      <div style={{
        position: "sticky", top: -28, zIndex: 10,
        background: "linear-gradient(180deg, #0B1020 75%, transparent)",
        padding: "16px 0 12px",
        marginBottom: 4,
      }}>
        <div style={{
          display: "flex", gap: 6, overflowX: "auto",
          paddingBottom: 2,
        }}>
          {SECTION_LIST.map(({ id, labelEn, labelRu, color }) => {
            const label = locale === "ru" ? labelRu : labelEn;
            const active = activeSection === id;
            return (
              <button
                key={id}
                onClick={() => scrollTo(id)}
                style={{
                  display: "inline-flex", alignItems: "center", gap: 6,
                  padding: "7px 14px", borderRadius: 20, flexShrink: 0,
                  fontFamily: "var(--font-mono)", fontSize: 11, fontWeight: 600,
                  letterSpacing: "0.06em",
                  cursor: "pointer",
                  transition: "all 150ms ease",
                  border: active ? `1px solid ${color}` : "1px solid #2E3B5A",
                  background: active ? `${color}18` : "transparent",
                  color: active ? color : "#64748B",
                  textTransform: "uppercase",
                }}
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>

      {/* ═══════════════════════════
          SECTION 1: Getting Started
      ═══════════════════════════ */}
      <div className="card" style={{ overflow: "hidden", marginBottom: 20 }}>
        <SectionHeading
          id="guide-start"
          illustration={<IllustrationGate />}
          accentColor="#60A5FA"
          tag={c(locale, "Getting Started", "Начало приключения") as string}
          title={c(locale, "Welcome to VultWake", "Добро пожаловать в VultWake")}
          subtitle={c(
            locale,
            "An idle dungeon RPG where your hero ventures into the dark while you manage their equipment and growth.",
            "Пошаговая RPG с простоем, где ваш герой отправляется в опасные данжи, пока вы управляете его снаряжением и развитием."
          )}
        />

        <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 16 }}>

          {/* Game loop heading */}
          <div style={{
            fontFamily: "var(--font-cinzel)", fontSize: 14, fontWeight: 600,
            letterSpacing: "0.06em", color: "#94A3B8", textTransform: "uppercase",
          }}>
            {c(locale, "The Core Loop", "Игровой цикл")}
          </div>

          {/* Step flow */}
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {[
              {
                num: 1, color: "#60A5FA",
                titleEn: "Create your hero", titleRu: "Создайте героя",
                bodyEn: "Choose a name and a class. Each class has a unique stat profile and visual. This is done once.",
                bodyRu: "Выберите имя и класс. Каждый класс обладает уникальным профилем характеристик. Это делается один раз.",
              },
              {
                num: 2, color: "#A855F7",
                titleEn: "Choose a dungeon", titleRu: "Выберите данж",
                bodyEn: "Browse available dungeons on the Dungeons screen. Each shows difficulty, duration, and your success chance.",
                bodyRu: "Изучите доступные данжи на экране Данжи. Каждый показывает сложность, длительность и шанс успеха.",
              },
              {
                num: 3, color: "#38BDF8",
                titleEn: "Send your hero on an expedition", titleRu: "Отправьте героя в поход",
                bodyEn: "Press Send Hero. Your hero sets off — you can track the timer and progress bar in real time.",
                bodyRu: "Нажмите «Отправить героя». Герой отправляется в путь — следите за таймером и полосой прогресса.",
              },
              {
                num: 4, color: "#22C55E",
                titleEn: "Play Rune Pairs to speed up (optional)", titleRu: "Сыграйте в Рунные Пары (необязательно)",
                bodyEn: "While the hero is away, tap Speed Up to play a memory match mini-game. Match all pairs before time runs out to cut remaining expedition time.",
                bodyRu: "Пока герой в походе, нажмите «Ускорить» и сыграйте в игру на память. Найдите все пары до истечения времени, чтобы сократить оставшееся время похода.",
              },
              {
                num: 5, color: "#F59E0B",
                titleEn: "Claim your reward", titleRu: "Заберите награду",
                bodyEn: "Once the run finishes, claim XP, copper coins, crafting ingredients, and possibly a loot item. Your hero can immediately go on the next expedition.",
                bodyRu: "По завершении похода заберите опыт, медные монеты, ингредиенты для крафта и, возможно, предмет снаряжения. Герой сразу готов к следующему походу.",
              },
              {
                num: 6, color: "#EF4444",
                titleEn: "Equip better gear & repeat", titleRu: "Наденьте лучшее снаряжение и повторяйте",
                bodyEn: "Equip loot to raise your hero's Power. Higher Power means better success chance in harder dungeons — which drop rarer loot.",
                bodyRu: "Экипируйте добычу, чтобы увеличить Мощь героя. Больше Мощи = выше шанс успеха в сложных данжах, которые дают более редкий лут.",
              },
            ].map(({ num, color, titleEn, titleRu, bodyEn, bodyRu }) => (
              <StepCard
                key={num}
                num={num}
                color={color}
                title={c(locale, titleEn, titleRu)}
                body={c(locale, bodyEn, bodyRu)}
              />
            ))}
          </div>

          <div className="divider" />

          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <TipBox tone="info">
              {c(locale,
                "Your hero can only be on one expedition at a time. Plan wisely — send them to dungeons suited to their current Power level.",
                "Ваш герой может находиться только в одном походе одновременно. Планируйте мудро — выбирайте данжи под текущий уровень Мощи."
              )}
            </TipBox>
            <TipBox tone="good">
              {c(locale,
                "You don't need to be online! Your hero completes expeditions in the background. Check back later to claim your rewards.",
                "Необязательно быть онлайн! Герой завершает походы в фоновом режиме. Заходите позже и забирайте награды."
              )}
            </TipBox>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════
          SECTION 2: Dungeons
      ═══════════════════════════ */}
      <div className="card" style={{ overflow: "hidden", marginBottom: 20 }}>
        <SectionHeading
          id="guide-dungeons"
          illustration={<IllustrationHourglass />}
          accentColor="#A855F7"
          tag={c(locale, "Expedition Guide", "Руководство по походам") as string}
          title={c(locale, "Dungeons of VultWake", "Данжи VultWake")}
          subtitle={c(
            locale,
            "Each dungeon is a timed expedition. The outcome depends on your hero's Power vs. the dungeon's difficulty.",
            "Каждый данж — это поход с таймером. Результат зависит от Мощи вашего героя и сложности данжа."
          )}
        />

        <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 18 }}>

          {/* Dungeon card anatomy */}
          <div>
            <div style={{
              fontFamily: "var(--font-cinzel)", fontSize: 13, fontWeight: 600,
              letterSpacing: "0.06em", color: "#94A3B8", textTransform: "uppercase",
              marginBottom: 10,
            }}>
              {c(locale, "Reading a Dungeon Card", "Как читать карточку данжа")}
            </div>
            <div style={{
              background: "#111827", border: "1px solid #2E3B5A", borderRadius: 12,
              padding: "14px 16px", display: "flex", flexDirection: "column", gap: 1,
            }}>
              <InfoRow
                label={c(locale, "Duration", "Длительность")}
                value={c(locale, "Time the expedition takes (shown on card)", "Время похода (показано на карточке)")}
                accent="#60A5FA"
              />
              <InfoRow
                label={c(locale, "Success Chance %", "Шанс успеха %")}
                value={c(locale, "Based on your hero's Power vs. dungeon difficulty", "Рассчитывается из Мощи героя и сложности данжа")}
                accent="#22C55E"
              />
              <InfoRow
                label={c(locale, "Loot Pool", "Пул лута")}
                value={c(locale, "See possible drops by pressing the ⓘ info button", "Нажмите кнопку ⓘ, чтобы увидеть возможные предметы")}
                accent="#F59E0B"
              />
            </div>
          </div>

          {/* Success chance explained */}
          <div style={{
            background: "linear-gradient(135deg, rgba(168,85,247,0.08), rgba(11,16,32,0.5))",
            border: "1px solid rgba(168,85,247,0.25)", borderRadius: 10,
            padding: "14px 16px",
          }}>
            <div style={{
              fontFamily: "var(--font-cinzel)", fontSize: 13, fontWeight: 600,
              color: "#D8B4FE", marginBottom: 8,
            }}>
              {c(locale, "How Success Chance Works", "Как работает шанс успеха")}
            </div>
            <div style={{ fontSize: 12, color: "#94A3B8", lineHeight: 1.65 }}>
              {c(locale,
                "Your hero's Power score is compared against the dungeon's minimum requirement. The closer your Power is to (or exceeds) the requirement, the higher your success chance. A failed expedition still returns your hero safely — they just earn less XP and no loot.",
                "Мощь вашего героя сравнивается с минимальным требованием данжа. Чем выше ваша Мощь относительно требования, тем выше шанс успеха. Провалившийся поход всё равно возвращает героя живым — он просто получает меньше опыта и не приносит лута."
              )}
            </div>
          </div>

          {/* Mini-game */}
          <div>
            <div style={{
              fontFamily: "var(--font-cinzel)", fontSize: 13, fontWeight: 600,
              letterSpacing: "0.06em", color: "#94A3B8", textTransform: "uppercase",
              marginBottom: 10,
            }}>
              {c(locale, "Rune Pairs Mini-Game", "Мини-игра «Рунные Пары»")}
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <div style={{ fontSize: 12, color: "#94A3B8", lineHeight: 1.65 }}>
                {c(locale,
                  "While your hero is on an active expedition, a Speed Up button appears. Tap it to launch the Rune Pairs memory game — flip cards and find all matching pairs before the mini-game timer runs out.",
                  "Пока герой в активном походе, появляется кнопка «Ускорить». Нажмите её, чтобы запустить игру «Рунные Пары» — переворачивайте карточки и находите все совпадающие пары до истечения таймера мини-игры."
                )}
              </div>
              <TipBox tone="info">
                {c(locale,
                  "Success: the remaining expedition time is reduced by the mini-game bonus. Fail: no penalty — the expedition continues normally.",
                  "Успех: оставшееся время похода сокращается на бонус мини-игры. Провал: штрафа нет — поход продолжается в обычном режиме."
                )}
              </TipBox>
            </div>
          </div>

        </div>
      </div>

      {/* ═══════════════════════════
          SECTION 3: Equipment
      ═══════════════════════════ */}
      <div className="card" style={{ overflow: "hidden", marginBottom: 20 }}>
        <SectionHeading
          id="guide-equipment"
          illustration={<IllustrationEquipment />}
          accentColor="#38BDF8"
          tag={c(locale, "Arms & Armour", "Оружие и броня") as string}
          title={c(locale, "Equipment System", "Система экипировки")}
          subtitle={c(
            locale,
            "Your hero has 5 equipment slots. Each equipped item directly boosts your combat stats.",
            "У героя 5 слотов экипировки. Каждый надетый предмет напрямую повышает боевые характеристики."
          )}
        />

        <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 18 }}>

          {/* Slot grid */}
          <div>
            <div style={{
              fontFamily: "var(--font-cinzel)", fontSize: 13, fontWeight: 600,
              letterSpacing: "0.06em", color: "#94A3B8", textTransform: "uppercase",
              marginBottom: 10,
            }}>
              {c(locale, "5 Equipment Slots", "5 слотов экипировки")}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(130px, 1fr))", gap: 8 }}>
              {[
                { enName: "Weapon",  ruName: "Оружие",   desc: c(locale, "Increases Attack", "Увеличивает Атаку") },
                { enName: "Helmet",  ruName: "Шлем",     desc: c(locale, "Increases Defense", "Увеличивает Защиту") },
                { enName: "Armor",   ruName: "Броня",    desc: c(locale, "Increases Health", "Увеличивает Здоровье") },
                { enName: "Boots",   ruName: "Ботинки",  desc: c(locale, "Increases Evasion", "Увеличивает Уклонение") },
                { enName: "Ring",    ruName: "Кольцо",   desc: c(locale, "Increases Critical", "Увеличивает Крит") },
              ].map(({ enName, ruName, desc }) => {
                const slotName = locale === "ru" ? ruName : enName;
                const icon = locale === "ru" ? SLOT_ICONS_RU[ruName] : SLOT_ICONS[enName];
                return (
                  <div key={enName} style={{
                    padding: "10px 12px",
                    background: "#111827", border: "1px solid #2E3B5A", borderRadius: 10,
                    display: "flex", alignItems: "center", gap: 10,
                  }}>
                    <span style={{
                      width: 30, height: 30, flexShrink: 0,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      background: "#1A2235", border: "1px solid #2E3B5A", borderRadius: 8,
                      fontSize: 14, color: "#60A5FA",
                    }}>{icon}</span>
                    <div>
                      <div style={{ fontSize: 12, fontWeight: 600, color: "#E5E7EB" }}>{slotName}</div>
                      <div style={{ fontSize: 11, color: "#64748B" }}>{desc}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="divider" />

          {/* How to equip */}
          <div>
            <div style={{
              fontFamily: "var(--font-cinzel)", fontSize: 13, fontWeight: 600,
              letterSpacing: "0.06em", color: "#94A3B8", textTransform: "uppercase",
              marginBottom: 10,
            }}>
              {c(locale, "Managing Items", "Управление предметами")}
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <InfoRow
                label={c(locale, "To equip", "Надеть")}
                value={c(locale, "Click item in Inventory → press Equip", "Клик по предмету → нажать Экипировать")}
              />
              <InfoRow
                label={c(locale, "To unequip", "Снять")}
                value={c(locale, "Click equipped item → press Unequip", "Клик по экипированному → нажать Снять")}
              />
              <InfoRow
                label={c(locale, "Wrong class", "Чужой класс")}
                value={c(locale, "Class-restricted items can't be equipped", "Предметы других классов нельзя надеть")}
                accent="#F59E0B"
              />
            </div>
          </div>

          <div className="divider" />

          {/* Durability */}
          <div>
            <div style={{
              fontFamily: "var(--font-cinzel)", fontSize: 13, fontWeight: 600,
              letterSpacing: "0.06em", color: "#94A3B8", textTransform: "uppercase",
              marginBottom: 10,
            }}>
              {c(locale, "Durability & Repairs", "Прочность и ремонт")}
            </div>
            <div style={{ fontSize: 12, color: "#94A3B8", lineHeight: 1.65, marginBottom: 10 }}>
              {c(locale,
                "Items lose durability each dungeon run. A colored number shows the current durability on each item cell. Red means the item is broken — repair it before your next expedition.",
                "Предметы теряют прочность после каждого похода. Цветной номер на ячейке предмета показывает текущую прочность. Красный = предмет сломан — почините его перед следующим походом."
              )}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
              {[
                { labelEn: "Good",   labelRu: "Хорошо",  color: "#22C55E",  desc: c(locale, "100% – 50%", "100% – 50%") },
                { labelEn: "Worn",   labelRu: "Изношен", color: "#F59E0B",  desc: c(locale, "49% – 25%", "49% – 25%") },
                { labelEn: "Broken", labelRu: "Сломан",  color: "#EF4444",  desc: c(locale, "< 25%", "< 25%") },
              ].map(({ labelEn, labelRu, color, desc }) => (
                <div key={labelEn} style={{
                  padding: "10px 12px", borderRadius: 8,
                  background: `${color}10`, border: `1px solid ${color}40`,
                  textAlign: "center",
                }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color, letterSpacing: "0.06em", textTransform: "uppercase" }}>
                    {locale === "ru" ? labelRu : labelEn}
                  </div>
                  <div style={{
                    fontFamily: "var(--font-mono)", fontSize: 12, color: "#E5E7EB", marginTop: 3,
                  }}>{desc}</div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 10 }}>
              <TipBox tone="warn">
                {c(locale,
                  "Broken items must be repaired before equipping. Go to Inventory → select the item → press Repair. The cost is shown in copper coins.",
                  "Сломанные предметы нужно починить перед экипировкой. Откройте Инвентарь → выберите предмет → нажмите «Ремонт». Стоимость показана в медных монетах."
                )}
              </TipBox>
            </div>
          </div>

          <div className="divider" />

          {/* Item Level */}
          <div>
            <div style={{
              fontFamily: "var(--font-cinzel)", fontSize: 13, fontWeight: 600,
              letterSpacing: "0.06em", color: "#94A3B8", textTransform: "uppercase",
              marginBottom: 10,
            }}>
              {c(locale, "Item Level", "Уровень предмета")}
            </div>
            <div style={{ fontSize: 12, color: "#94A3B8", lineHeight: 1.65, marginBottom: 10 }}>
              {c(locale,
                "Every dropped or purchased item has an Item Level — a quality score that scales all of its stats. Two items with the same rarity and stat types can differ significantly in strength if their item levels differ.",
                "У каждого выпавшего или купленного предмета есть Уровень предмета — показатель качества, который масштабирует все его характеристики. Два предмета с одинаковой редкостью и типами статов могут значительно различаться по силе из-за разного уровня предмета."
              )}
            </div>
            <div style={{
              background: "linear-gradient(135deg, rgba(56,189,248,0.08), rgba(11,16,32,0.5))",
              border: "1px solid rgba(56,189,248,0.25)", borderRadius: 10,
              padding: "14px 16px", marginBottom: 10,
            }}>
              <div style={{
                fontFamily: "var(--font-mono)", fontSize: 13,
                color: "#E5E7EB", letterSpacing: "0.04em", lineHeight: 1.8,
              }}>
                <span style={{ color: "#38BDF8", fontWeight: 700 }}>
                  {c(locale, "Final stat", "Итоговый стат")}
                </span>
                {" = "}
                <span style={{ color: "#94A3B8" }}>{c(locale, "base", "база")}</span>
                {" × "}
                <span style={{ color: "#A855F7" }}>{c(locale, "rarity mult", "множитель редкости")}</span>
                {" × (1 + "}
                <span style={{ color: "#F59E0B" }}>{c(locale, "item level", "уровень предмета")}</span>
                {" × 0.025)"}
              </div>
              <div style={{ marginTop: 10, fontSize: 12, color: "#64748B", lineHeight: 1.5 }}>
                {c(locale,
                  "Each item level adds +2.5% to every stat. A level 10 item has +25% stronger stats than a level 1 item of the same rarity.",
                  "Каждый уровень предмета добавляет +2,5% к каждому стату. Предмет 10-го уровня имеет на +25% более сильные характеристики, чем предмет 1-го уровня той же редкости."
                )}
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 1, marginBottom: 10 }}>
              <InfoRow
                label={c(locale, "How level is set", "Как задаётся уровень")}
                value={c(locale, "Rolled randomly within the rarity's range at drop time", "Случайно выбирается в диапазоне редкости при выпадении")}
                accent="#38BDF8"
              />
              <InfoRow
                label={c(locale, "Can it be upgraded?", "Можно ли улучшить?")}
                value={c(locale, "No — fixed at creation", "Нет — фиксируется при создании")}
                accent="#F59E0B"
              />
            </div>
            <TipBox tone="info">
              {c(locale,
                "Item level is shown on each item card in your Inventory. When comparing two items of the same rarity, the one with a higher item level will generally have stronger stats.",
                "Уровень предмета отображается на карточке каждого предмета в инвентаре. При сравнении двух предметов одной редкости тот, у которого выше уровень предмета, как правило, окажется сильнее."
              )}
            </TipBox>
          </div>

        </div>
      </div>

      {/* ═══════════════════════════
          SECTION 4: Rarity
      ═══════════════════════════ */}
      <div className="card" style={{ overflow: "hidden", marginBottom: 20 }}>
        <SectionHeading
          id="guide-rarity"
          illustration={<IllustrationGems />}
          accentColor="#F59E0B"
          tag={c(locale, "Item Quality", "Качество предметов") as string}
          title={c(locale, "Rarity Tiers", "Уровни редкости")}
          subtitle={c(
            locale,
            "Every item has a rarity tier. Higher rarity means stronger stats and a distinctive glow border in your inventory.",
            "У каждого предмета есть уровень редкости. Выше редкость — сильнее характеристики и заметнее свечение в инвентаре."
          )}
        />

        <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 18 }}>

          {/* Rarity grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))", gap: 8 }}>
            {RARITIES.map(({ key, label, nameEn, nameRu, color, border, bg }) => (
              <div key={key} style={{
                padding: "12px 10px", borderRadius: 10,
                background: bg, border: `1.5px solid ${border}`,
                display: "flex", flexDirection: "column", alignItems: "center", gap: 4,
                boxShadow: `0 0 12px ${color}18`,
              }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 8,
                  background: "#0B1020", border: `1.5px solid ${border}`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontFamily: "var(--font-mono)", fontSize: 14, fontWeight: 800, color,
                  boxShadow: `0 0 10px ${color}35`,
                }}>{label}</div>
                <div style={{
                  fontFamily: "var(--font-cinzel)", fontSize: 11, fontWeight: 700,
                  color, letterSpacing: "0.04em", textAlign: "center",
                }}>{locale === "ru" ? nameRu : nameEn}</div>
              </div>
            ))}
          </div>

          <TipBox tone="info">
            {c(locale,
              "Rarity is fixed at drop time and cannot be upgraded. Focus on equipping the highest-rarity items available for your hero's class and level.",
              "Редкость фиксируется при выпадении и не может быть улучшена. Старайтесь экипировать предметы максимальной редкости, доступные для вашего класса и уровня."
            )}
          </TipBox>

          <div style={{ fontSize: 12, color: "#94A3B8", lineHeight: 1.65 }}>
            {c(locale,
              "Harder dungeons have a higher chance to drop rarer items. As your Power grows, unlock new dungeons with better loot pools. The rarity border glows on every item in your inventory, making it easy to spot valuable pieces at a glance.",
              "В более сложных данжах выше шанс выпадения редких предметов. По мере роста Мощи открываются новые данжи с более ценным лутом. Граница редкости светится на каждом предмете в инвентаре — это позволяет с первого взгляда определить ценные вещи."
            )}
          </div>

          <TipBox tone="info">
            {c(locale,
              "Each rarity tier also determines the Item Level range that can be rolled when the item drops. Higher rarities unlock higher item level ranges — meaning rarer items receive a larger stat bonus on top of their rarity multiplier. See the Equipment section for details.",
              "Каждый уровень редкости также определяет диапазон Уровня предмета, который может выпасть. Более высокие редкости открывают более высокие диапазоны уровней — это значит, что редкие предметы получают дополнительный бонус к статам поверх множителя редкости. Подробности — в разделе «Экипировка»."
            )}
          </TipBox>

        </div>
      </div>

      {/* ═══════════════════════════
          SECTION 5: Stats
      ═══════════════════════════ */}
      <div className="card" style={{ overflow: "hidden", marginBottom: 20 }}>
        <SectionHeading
          id="guide-stats"
          illustration={<IllustrationStats />}
          accentColor="#22C55E"
          tag={c(locale, "Combat Doctrine", "Боевая доктрина") as string}
          title={c(locale, "Stats & Power", "Характеристики и Мощь")}
          subtitle={c(
            locale,
            "Five core stats define your hero's combat effectiveness. Power is the combined score that drives dungeon success chance.",
            "Пять основных характеристик определяют боевую эффективность героя. Мощь — это суммарный показатель, влияющий на шанс успеха в данже."
          )}
        />

        <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 18 }}>

          {/* Stats table */}
          <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
            {[
              {
                key: "intellect",  icon: "✸", color: "#A855F7",
                labelEn: "Intellect", labelRu: "Интеллект",
                descEn: "Arcane aptitude. A core Power stat that boosts your overall combat score.",
                descRu: "Магическая одарённость. Базовая характеристика Мощи, повышающая общий боевой показатель.",
              },
              {
                key: "attack",     icon: "⚔", color: "#3B82F6",
                labelEn: "Attack",   labelRu: "Атака",
                descEn: "Physical damage dealt per strike. The most impactful stat for Power calculation.",
                descRu: "Физический урон за удар. Наиболее весомая характеристика при расчёте Мощи.",
              },
              {
                key: "defense",    icon: "⛨", color: "#60A5FA",
                labelEn: "Defense",  labelRu: "Защита",
                descEn: "Damage reduction in combat. Second highest weight in Power calculation.",
                descRu: "Снижение урона в бою. Второй по значимости вес в расчёте Мощи.",
              },
              {
                key: "critical",   icon: "✦", color: "#F59E0B",
                labelEn: "Critical", labelRu: "Крит",
                descEn: "Probability of landing a critical hit that deals bonus damage.",
                descRu: "Вероятность нанести критический удар с бонусным уроном.",
              },
              {
                key: "evasion",    icon: "◌", color: "#22C55E",
                labelEn: "Evasion",  labelRu: "Уклонение",
                descEn: "Chance to dodge incoming attacks entirely.",
                descRu: "Шанс полностью уклониться от входящей атаки.",
              },
            ].map(({ key, icon, color, labelEn, labelRu, descEn, descRu }) => (
              <div key={key} style={{
                display: "flex", alignItems: "flex-start", gap: 12,
                padding: "10px 12px",
                background: "#111827", border: "1px solid #243150",
                borderLeft: `3px solid ${color}`,
                borderRadius: 8, marginBottom: 4,
              }}>
                <div style={{
                  width: 28, height: 28, flexShrink: 0,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  background: `${color}18`, border: `1px solid ${color}50`,
                  borderRadius: 6, fontSize: 13, color,
                }}>{icon}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "#E5E7EB", marginBottom: 2 }}>
                    {locale === "ru" ? labelRu : labelEn}
                  </div>
                  <div style={{ fontSize: 12, color: "#94A3B8", lineHeight: 1.5 }}>
                    {c(locale, descEn, descRu)}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="divider" />

          {/* Power formula */}
          <div>
            <div style={{
              fontFamily: "var(--font-cinzel)", fontSize: 13, fontWeight: 600,
              letterSpacing: "0.06em", color: "#94A3B8", textTransform: "uppercase",
              marginBottom: 10,
            }}>
              {c(locale, "Power Formula", "Формула Мощи")}
            </div>
            <div style={{
              background: "linear-gradient(135deg, rgba(34,197,94,0.08), rgba(11,16,32,0.5))",
              border: "1px solid rgba(34,197,94,0.25)", borderRadius: 10,
              padding: "16px 18px",
            }}>
              <div style={{
                fontFamily: "var(--font-mono)", fontSize: 13,
                color: "#E5E7EB", letterSpacing: "0.04em", lineHeight: 1.8,
              }}>
                <span style={{ color: "#22C55E", fontWeight: 700 }}>
                  {c(locale, "Power", "Мощь")} =
                </span>
                {" "}
                <span style={{ color: "#3B82F6" }}>{c(locale, "ATK", "АТК")} × 2.0</span>
                {" + "}
                <span style={{ color: "#60A5FA" }}>{c(locale, "DEF", "ЗАЩ")} × 1.7</span>
                {" + "}
                <span style={{ color: "#A855F7" }}>{c(locale, "INT", "ИНТ")} × 1.5</span>
                {" + "}
                <span style={{ color: "#F59E0B" }}>{c(locale, "CRIT", "КРТ")} × 1.5</span>
                {" + "}
                <span style={{ color: "#22C55E" }}>{c(locale, "EVA", "УКЛ")} × 1.5</span>
              </div>
              <div style={{ marginTop: 10, fontSize: 12, color: "#64748B", lineHeight: 1.5 }}>
                {c(locale,
                  "Attack and Defense are weighted most heavily. Prioritize items with high ATK or DEF for the best Power gains.",
                  "Атака и Защита имеют наибольший вес. Приоритизируйте предметы с высоким АТК или ЗАЩ для максимального прироста Мощи."
                )}
              </div>
            </div>
          </div>

          <TipBox tone="good">
            {c(locale,
              "Hover over the Power value on the Character screen (or tap ⓘ on mobile) to see a live breakdown of your Power components.",
              "Наведите курсор на значение Мощи на экране Персонажа (или нажмите ⓘ на мобильном), чтобы увидеть детальный расчёт."
            )}
          </TipBox>

        </div>
      </div>

      {/* ═══════════════════════════
          SECTION: Potions & Brewing
      ═══════════════════════════ */}
      <div className="card" style={{ overflow: "hidden", marginBottom: 20 }}>
        <SectionHeading
          id="guide-alchemy"
          illustration={<IllustrationPotion />}
          accentColor="#14B8A6"
          tag={c(locale, "Alchemy & Consumables", "Алхимия и расходники") as string}
          title={c(locale, "Potions & Brewing", "Зелья и варка")}
          subtitle={c(
            locale,
            "Gather ingredients, brew them into potions, and drink potions to restore your hero's health between expeditions.",
            "Собирайте ингредиенты, варите из них зелья и пейте зелья, чтобы восстанавливать здоровье героя между походами."
          )}
        />

        <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 18 }}>

          {/* Consumable types */}
          <div>
            <div style={{
              fontFamily: "var(--font-cinzel)", fontSize: 13, fontWeight: 600,
              letterSpacing: "0.06em", color: "#94A3B8", textTransform: "uppercase",
              marginBottom: 10,
            }}>
              {c(locale, "Two Kinds of Consumables", "Два вида расходников")}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {[
                {
                  icon: "🌿", color: "#22C55E",
                  titleEn: "Ingredients", titleRu: "Ингредиенты",
                  bodyEn: "Raw crafting materials dropped by dungeons or bought in the Shop. They have no direct use — combine them to brew potions.",
                  bodyRu: "Сырьё для крафта, выпадает в данжах или покупается в Магазине. Сами по себе бесполезны — из них варят зелья.",
                },
                {
                  icon: "⚗", color: "#14B8A6",
                  titleEn: "Potions", titleRu: "Зелья",
                  bodyEn: "Consumables that heal a percentage of your hero's max HP when used. Find them in Inventory → Consumables.",
                  bodyRu: "Расходники, восстанавливающие процент от макс. HP героя при использовании. Ищите их в Инвентарь → Расходники.",
                },
              ].map(({ icon, color, titleEn, titleRu, bodyEn, bodyRu }) => (
                <div key={titleEn} style={{
                  padding: "12px 14px", borderRadius: 10,
                  background: "#111827", border: "1px solid #2E3B5A",
                  borderLeft: `3px solid ${color}`,
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                    <span style={{ fontSize: 15 }}>{icon}</span>
                    <span style={{ fontSize: 13, fontWeight: 600, color: "#E5E7EB" }}>{c(locale, titleEn, titleRu)}</span>
                  </div>
                  <div style={{ fontSize: 12, color: "#94A3B8", lineHeight: 1.5 }}>{c(locale, bodyEn, bodyRu)}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="divider" />

          {/* Brewing steps */}
          <div>
            <div style={{
              fontFamily: "var(--font-cinzel)", fontSize: 13, fontWeight: 600,
              letterSpacing: "0.06em", color: "#94A3B8", textTransform: "uppercase",
              marginBottom: 10,
            }}>
              {c(locale, "Brewing Potions", "Варка зелий")}
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {[
                {
                  num: 1, color: "#14B8A6",
                  titleEn: "Open the Brewing panel", titleRu: "Откройте панель варки",
                  bodyEn: "Go to Inventory → Consumables. The Brewing panel lists every recipe you can learn.",
                  bodyRu: "Откройте Инвентарь → Расходники. Панель «Варка зелий» показывает все доступные рецепты.",
                },
                {
                  num: 2, color: "#38BDF8",
                  titleEn: "Pick a recipe difficulty", titleRu: "Выберите сложность рецепта",
                  bodyEn: "Recipes come in Small, Medium and Large tiers. Larger recipes need rarer ingredients and a higher hero level, but yield stronger potions.",
                  bodyRu: "Рецепты бывают Малой, Средней и Большой сложности. Сложные требуют более редких ингредиентов и уровня героя, но дают более сильные зелья.",
                },
                {
                  num: 3, color: "#22C55E",
                  titleEn: "Check your ingredients", titleRu: "Проверьте ингредиенты",
                  bodyEn: "Each recipe shows the ingredients required and how many you own. Missing ones are highlighted.",
                  bodyRu: "Каждый рецепт показывает нужные ингредиенты и сколько у вас есть. Недостающие подсвечиваются.",
                },
                {
                  num: 4, color: "#F59E0B",
                  titleEn: "Set the batch size & brew", titleRu: "Задайте размер партии и варите",
                  bodyEn: "Use the stepper to brew several potions at once (limited by your ingredients), then press Create.",
                  bodyRu: "С помощью счётчика сварите несколько зелий сразу (в пределах ваших ингредиентов) и нажмите «Создать».",
                },
              ].map(({ num, color, titleEn, titleRu, bodyEn, bodyRu }) => (
                <StepCard key={num} num={num} color={color} title={c(locale, titleEn, titleRu)} body={c(locale, bodyEn, bodyRu)} />
              ))}
            </div>
          </div>

          <TipBox tone="good">
            {c(locale,
              "Brew potions while your hero rests, then drink one before a risky expedition. Higher max HP from gear means each percent-based heal restores more.",
              "Варите зелья, пока герой отдыхает, и выпивайте перед опасным походом. Чем выше макс. HP от снаряжения, тем больше восстанавливает каждое зелье в процентах."
            )}
          </TipBox>

        </div>
      </div>

      {/* ═══════════════════════════
          SECTION: Shop & Premium
      ═══════════════════════════ */}
      <div className="card" style={{ overflow: "hidden", marginBottom: 20 }}>
        <SectionHeading
          id="guide-shop"
          illustration={<IllustrationShop />}
          accentColor="#C084FC"
          tag={c(locale, "Marketplace", "Торговая лавка") as string}
          title={c(locale, "Shop & Premium", "Магазин и Премиум")}
          subtitle={c(
            locale,
            "Spend copper or premium gems on offers that grant items, potions, ingredients, or whole chests of loot.",
            "Тратьте медь или премиум-самоцветы на предложения, дающие предметы, зелья, ингредиенты или целые сундуки с лутом."
          )}
        />

        <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 18 }}>

          {/* What you can buy */}
          <div>
            <div style={{
              fontFamily: "var(--font-cinzel)", fontSize: 13, fontWeight: 600,
              letterSpacing: "0.06em", color: "#94A3B8", textTransform: "uppercase",
              marginBottom: 10,
            }}>
              {c(locale, "Reading an Offer", "Как читать предложение")}
            </div>
            <div style={{
              background: "#111827", border: "1px solid #2E3B5A", borderRadius: 12,
              padding: "14px 16px", display: "flex", flexDirection: "column", gap: 1,
            }}>
              <InfoRow
                label={c(locale, "Reward kind", "Тип награды")}
                value={c(locale, "Item · Potion · Ingredient", "Предмет · Зелье · Ингредиент")}
                accent="#60A5FA"
              />
              <InfoRow
                label={c(locale, "Delivery: Single", "Доставка: Один")}
                value={c(locale, "A fixed reward you get every time", "Фиксированная награда каждый раз")}
                accent="#22C55E"
              />
              <InfoRow
                label={c(locale, "Delivery: Chest ×N", "Доставка: Сундук ×N")}
                value={c(locale, "Rolls N random rewards from a drop table", "Выдаёт N случайных наград из таблицы дропа")}
                accent="#F59E0B"
              />
              <InfoRow
                label={c(locale, "Price", "Цена")}
                value={c(locale, "Copper and/or premium gems 💎", "Медь и/или премиум-самоцветы 💎")}
                accent="#C084FC"
              />
            </div>
          </div>

          {/* Chests explained */}
          <div style={{
            background: "linear-gradient(135deg, rgba(192,132,252,0.08), rgba(11,16,32,0.5))",
            border: "1px solid rgba(192,132,252,0.25)", borderRadius: 10,
            padding: "14px 16px",
          }}>
            <div style={{
              fontFamily: "var(--font-cinzel)", fontSize: 13, fontWeight: 600,
              color: "#E9D5FF", marginBottom: 8,
            }}>
              {c(locale, "Chests & Drop Chances", "Сундуки и шансы дропа")}
            </div>
            <div style={{ fontSize: 12, color: "#94A3B8", lineHeight: 1.65 }}>
              {c(locale,
                "Open an offer to see its possible rewards, each with a drop chance %. Chest offers roll randomly from this table — set a purchase count to open several at once. After buying, the modal shows exactly what you received.",
                "Откройте предложение, чтобы увидеть возможные награды и шанс выпадения каждой. Сундуки берут награды случайно из этой таблицы — задайте количество покупок, чтобы открыть сразу несколько. После покупки в окне показано, что именно вы получили."
              )}
            </div>
          </div>

          <div className="divider" />

          {/* Premium & exchange */}
          <div>
            <div style={{
              fontFamily: "var(--font-cinzel)", fontSize: 13, fontWeight: 600,
              letterSpacing: "0.06em", color: "#94A3B8", textTransform: "uppercase",
              marginBottom: 10,
            }}>
              {c(locale, "Premium Gems & Exchange", "Премиум-самоцветы и обмен")}
            </div>
            <div style={{ fontSize: 12, color: "#94A3B8", lineHeight: 1.65, marginBottom: 10 }}>
              {c(locale,
                "Premium gems 💎 are a special currency shown next to your coins in the top bar. Some shop offers can be paid for in either copper or gems — pick your preferred currency before buying. Need more copper? Tap the + button beside your coin balance to open the Exchange and convert gems into copper.",
                "Премиум-самоцветы 💎 — особая валюта, показанная рядом с монетами в верхней панели. Некоторые предложения магазина можно оплатить медью или самоцветами — выберите валюту перед покупкой. Нужно больше меди? Нажмите кнопку + рядом с балансом монет, чтобы открыть Обмен и конвертировать самоцветы в медь."
              )}
            </div>
            <TipBox tone="info">
              {c(locale,
                "The Exchange only goes one way — gems into copper. Spend gems on premium offers first; exchange the rest when you need coins for repairs or crafting.",
                "Обмен работает только в одну сторону — самоцветы в медь. Сначала тратьте самоцветы на премиум-предложения, а остаток меняйте, когда нужна медь на ремонт или крафт."
              )}
            </TipBox>
          </div>

        </div>
      </div>

      {/* ═══════════════════════════
          SECTION 6: Currency
      ═══════════════════════════ */}
      <div className="card" style={{ overflow: "hidden", marginBottom: 20 }}>
        <SectionHeading
          id="guide-currency"
          illustration={<IllustrationCoins />}
          accentColor="#FBBF24"
          tag={c(locale, "Economy", "Экономика") as string}
          title={c(locale, "Coinage of VultWake", "Монеты VultWake")}
          subtitle={c(
            locale,
            "All wealth is measured in copper. The UI automatically converts large amounts to silver and gold.",
            "Всё богатство измеряется в меди. Интерфейс автоматически конвертирует большие суммы в серебро и золото."
          )}
        />

        <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 18 }}>

          {/* Conversion table */}
          <div>
            <div style={{
              fontFamily: "var(--font-cinzel)", fontSize: 13, fontWeight: 600,
              letterSpacing: "0.06em", color: "#94A3B8", textTransform: "uppercase",
              marginBottom: 10,
            }}>
              {c(locale, "Conversion Rates", "Обменные курсы")}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
              {[
                { coin: "copper", labelEn: "Copper",  labelRu: "Медь",   valEn: "1 unit",      valRu: "1 единица",     bg: "rgba(205,124,69,0.1)",  border: "rgba(241,168,119,0.4)", color: "#F1A877" },
                { coin: "silver", labelEn: "Silver",  labelRu: "Серебро", valEn: "= 100 copper", valRu: "= 100 меди",   bg: "rgba(203,213,225,0.1)", border: "rgba(203,213,225,0.4)", color: "#CBD5E1" },
                { coin: "gold",   labelEn: "Gold",    labelRu: "Золото",  valEn: "= 10 000 copper",valRu:"= 10 000 меди",bg: "rgba(251,191,36,0.1)",  border: "rgba(251,191,36,0.4)",  color: "#FBBF24" },
              ].map(({ coin, labelEn, labelRu, valEn, valRu, bg, border, color }) => (
                <div key={coin} style={{
                  padding: "14px 12px", borderRadius: 10, textAlign: "center",
                  background: bg, border: `1.5px solid ${border}`,
                }}>
                  <div style={{
                    fontFamily: "var(--font-cinzel)", fontSize: 16, fontWeight: 700,
                    color, marginBottom: 4,
                  }}>{locale === "ru" ? labelRu : labelEn}</div>
                  <div style={{
                    fontFamily: "var(--font-mono)", fontSize: 11, color: "#94A3B8",
                  }}>{locale === "ru" ? valRu : valEn}</div>
                </div>
              ))}
            </div>
          </div>

          <TipBox tone="info">
            {c(locale,
              "Premium gems 💎 are a separate currency and are not part of the copper/silver/gold scale. You can convert gems into copper via the Exchange — see the Shop & Premium section.",
              "Премиум-самоцветы 💎 — отдельная валюта и не входят в шкалу медь/серебро/золото. Самоцветы можно конвертировать в медь через Обмен — см. раздел «Магазин и Премиум»."
            )}
          </TipBox>

          <div className="divider" />

          {/* Earning & spending */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <div style={{
                fontFamily: "var(--font-cinzel)", fontSize: 12, fontWeight: 600,
                color: "#22C55E", textTransform: "uppercase", letterSpacing: "0.08em",
                marginBottom: 8,
              }}>{c(locale, "Earning", "Доходы")}</div>
              {[
                c(locale, "Completing dungeon runs", "Завершение данжей"),
                c(locale, "Claiming expedition rewards", "Получение наград"),
                c(locale, "Destroying unwanted items", "Уничтожение предметов"),
                c(locale, "Exchanging premium gems", "Обмен премиум-самоцветов"),
              ].map((item, i) => (
                <div key={i} style={{
                  display: "flex", alignItems: "center", gap: 8,
                  padding: "6px 0", borderBottom: "1px dashed #243150",
                  fontSize: 12, color: "#94A3B8",
                }}>
                  <span style={{ color: "#22C55E", fontSize: 10 }}>+</span>
                  {item}
                </div>
              ))}
            </div>
            <div>
              <div style={{
                fontFamily: "var(--font-cinzel)", fontSize: 12, fontWeight: 600,
                color: "#EF4444", textTransform: "uppercase", letterSpacing: "0.08em",
                marginBottom: 8,
              }}>{c(locale, "Spending", "Расходы")}</div>
              {[
                c(locale, "Repairing broken equipment", "Ремонт сломанного снаряжения"),
                c(locale, "Buying shop offers", "Покупки в магазине"),
                c(locale, "Repairing the full pack at once", "Ремонт всей сумки сразу"),
              ].map((item, i) => (
                <div key={i} style={{
                  display: "flex", alignItems: "center", gap: 8,
                  padding: "6px 0", borderBottom: "1px dashed #243150",
                  fontSize: 12, color: "#94A3B8",
                }}>
                  <span style={{ color: "#EF4444", fontSize: 10 }}>−</span>
                  {item}
                </div>
              ))}
            </div>
          </div>

          <TipBox tone="warn">
            {c(locale,
              "Keep a copper reserve for repairs. Broken gear that isn't repaired reduces your Power and hurts your success chance on the next expedition.",
              "Держите запас меди для ремонта. Сломанное снаряжение без починки снижает Мощь и ухудшает шанс успеха в следующем походе."
            )}
          </TipBox>

        </div>
      </div>

      {/* ═══════════════════════════
          TIPS FOOTER
      ═══════════════════════════ */}
      <div className="card" style={{ overflow: "hidden", marginBottom: 8 }}>
        <div style={{
          padding: "20px 24px 16px",
          borderTop: "3px solid #A855F7",
          background: "linear-gradient(135deg, rgba(168,85,247,0.07) 0%, transparent 60%)",
          borderRadius: "14px 14px 0 0",
          borderBottom: "1px solid #243150",
        }}>
          <div style={{
            fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.22em",
            textTransform: "uppercase", color: "#A855F7", marginBottom: 6,
          }}>{c(locale, "Quick Reference", "Быстрая справка")}</div>
          <h2 style={{
            fontFamily: "var(--font-cinzel)", fontSize: 20, fontWeight: 700,
            letterSpacing: "0.04em", color: "#F1F5F9", margin: 0,
          }}>{c(locale, "Beginner Tips", "Советы новичку")}</h2>
        </div>

        <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {[
            {
              tone: "good" as const,
              en: "Start with the easiest available dungeon that matches your Power — 100% success chance means guaranteed XP and a loot roll.",
              ru: "Начинайте с самого лёгкого данжа, подходящего вашей Мощи — 100% шанс успеха гарантирует XP и броск на лут.",
            },
            {
              tone: "info" as const,
              en: "Equip all 5 slots before your first real dungeon. Even F-rarity gear is better than an empty slot.",
              ru: "Заполните все 5 слотов перед первым серьёзным данжем. Даже снаряжение F-редкости лучше пустого слота.",
            },
            {
              tone: "info" as const,
              en: "The Leaderboard shows top heroes by level — compare your stats to know when you're ready to tackle the next tier of dungeons.",
              ru: "Таблица лидеров показывает топ героев по уровню — сравнивайте статы, чтобы понять, когда вы готовы к следующему уровню данжей.",
            },
            {
              tone: "warn" as const,
              en: "Don't destroy items immediately — check if it's better than your equipped gear first. An upgrade in any slot raises your Power.",
              ru: "Не уничтожайте предметы сразу — сначала проверьте, не лучше ли они вашего текущего снаряжения. Апгрейд в любом слоте увеличивает Мощь.",
            },
            {
              tone: "good" as const,
              en: "Play Rune Pairs every time your hero is on a long expedition — even a failed attempt has no downside, and success cuts wait time significantly.",
              ru: "Играйте в Рунные Пары каждый раз, когда герой в длинном походе — даже провальная попытка без штрафов, а успех значительно сокращает время ожидания.",
            },
            {
              tone: "info" as const,
              en: "Level up passively by completing runs. Higher level unlocks better gear rolls and increases your base stat growth.",
              ru: "Повышайте уровень пассивно, завершая походы. Более высокий уровень открывает лучшие предметы и увеличивает базовый прирост характеристик.",
            },
            {
              tone: "good" as const,
              en: "Keep a few healing potions brewed and ready — drinking one before a low-success dungeon can be the difference between a win and a wasted run.",
              ru: "Держите несколько лечебных зелий наготове — выпитое перед данжем с низким шансом успеха зелье может решить исход похода.",
            },
            {
              tone: "info" as const,
              en: "Check the Shop for chest offers — they roll random loot from a drop table and are a fast way to gather ingredients or chase rarer items.",
              ru: "Загляните в Магазин за сундуками — они дают случайный лут из таблицы дропа и быстро пополняют ингредиенты или приносят редкие предметы.",
            },
          ].map(({ tone, en, ru }, i) => (
            <TipBox key={i} tone={tone}>{c(locale, en, ru)}</TipBox>
          ))}

          <div style={{
            marginTop: 8, padding: "12px 16px",
            background: "#111827", border: "1px solid #2E3B5A",
            borderRadius: 8, display: "flex", justifyContent: "center",
          }}>
            <div style={{
              fontFamily: "var(--font-mono)", fontSize: 10,
              letterSpacing: "0.16em", textTransform: "uppercase",
              color: "#64748B",
            }}>
              {c(locale, "VultWake · Field Guide · v0.2", "VultWake · Руководство искателя · v0.2")}
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
