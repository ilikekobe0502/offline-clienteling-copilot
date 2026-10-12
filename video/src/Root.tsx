import React from 'react';
import { AbsoluteFill, Audio, Composition, Sequence, staticFile, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import durations from './durations.json';
import data from './data.json';

const FPS = 30;
const PAD = 0.8; // seconds of breathing room after each narration line
const C = { ink: '#0F172A', bg: '#F8FAFB', teal: '#0D9488', tealLight: '#5EEAD4', mint: '#CCFBF1', slate: '#475569', muted: '#94A3B8', card: '#FFFFFF', line: '#E2E8F0' };
const FONT = "'DM Sans', 'Helvetica Neue', Arial, sans-serif";
const MONO = "'JetBrains Mono', Menlo, monospace";

type SceneId = 's1' | 's2' | 's3' | 's4' | 's5' | 's6' | 's7' | 's8';
const ORDER: SceneId[] = ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8'];
const dur = (id: SceneId) => Math.round(((durations as Record<string, number>)[id] + PAD) * FPS);

const fadeIn = (frame: number, start = 0, len = 12) => interpolate(frame, [start, start + len], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
const rise = (frame: number, start = 0) => interpolate(frame, [start, start + 15], [24, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

const Eyebrow: React.FC<{ children: React.ReactNode; dark?: boolean }> = ({ children, dark }) => (
  <div style={{ fontSize: 26, fontWeight: 700, letterSpacing: 4, textTransform: 'uppercase', color: dark ? C.tealLight : C.teal }}>{children}</div>
);

/* ---------- S1: hook ---------- */
const S1: React.FC = () => {
  const f = useCurrentFrame();
  const facts = ['Ring size 11', 'Loves emeralds', 'Anniversary · Oct 22', 'Budget ~ NT$150k'];
  return (
    <AbsoluteFill style={{ background: C.ink, fontFamily: FONT, padding: 120, justifyContent: 'center', gap: 56 }}>
      <div style={{ opacity: fadeIn(f), transform: `translateY(${rise(f)}px)`, fontSize: 78, fontWeight: 700, color: '#F8FAFC', lineHeight: 1.1 }}>A great consultant remembers everything.</div>
      <div style={{ display: 'flex', gap: 28, flexWrap: 'wrap' }}>
        {facts.map((t, i) => (
          <div key={t} style={{ opacity: fadeIn(f, 40 + i * 25), transform: `translateY(${rise(f, 40 + i * 25)}px)`, background: '#1E293B', border: `2px solid ${C.teal}`, color: C.mint, fontSize: 40, padding: '22px 34px', borderRadius: 18 }}>{t}</div>
        ))}
      </div>
      <div style={{ opacity: fadeIn(f, 300), fontSize: 46, color: C.muted }}>…but between clients, there is no time to write it down.</div>
    </AbsoluteFill>
  );
};

/* ---------- S2: problem ---------- */
const S2: React.FC = () => {
  const f = useCurrentFrame();
  const items = [['Privacy law & policy', 'Client records restricted to approved processing'], ['Client trust', 'A VIP memo is the most sensitive thing in the store'], ['Store networks', 'Basements and shared Wi-Fi drop connections']];
  return (
    <AbsoluteFill style={{ background: C.bg, fontFamily: FONT, padding: 120, gap: 48 }}>
      <Eyebrow>The problem</Eyebrow>
      <div style={{ opacity: fadeIn(f, 90), fontSize: 92, fontWeight: 700, color: C.ink, lineHeight: 1.05 }}>"Where does the recording go?"</div>
      <div style={{ display: 'flex', gap: 32 }}>
        {items.map(([h, p], i) => (
          <div key={h} style={{ flex: 1, opacity: fadeIn(f, 220 + i * 40), transform: `translateY(${rise(f, 220 + i * 40)}px)`, background: C.card, border: `1px solid ${C.line}`, borderRadius: 22, padding: 40 }}>
            <div style={{ fontSize: 40, fontWeight: 700, color: C.ink }}>{h}</div>
            <div style={{ fontSize: 30, color: C.slate, marginTop: 14, lineHeight: 1.4 }}>{p}</div>
          </div>
        ))}
      </div>
      <div style={{ opacity: fadeIn(f, 480), fontSize: 46, fontWeight: 700, color: C.teal }}>The cloud is the wrong place for this.</div>
    </AbsoluteFill>
  );
};

/* ---------- S3: solution ---------- */
const S3: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const steps = [['Speak', '30-second memo'], ['On-device AI', 'ASUS UGen300'], ['Client record', 'Saved locally']];
  return (
    <AbsoluteFill style={{ background: `linear-gradient(135deg, ${C.ink}, #10302E)`, fontFamily: FONT, padding: 120, justifyContent: 'center', gap: 64 }}>
      <Eyebrow dark>Introducing</Eyebrow>
      <div style={{ fontSize: 110, fontWeight: 700, color: '#F8FAFC', transform: `scale(${spring({ frame: f, fps, config: { damping: 200 } })})`, transformOrigin: 'left' }}>Offline Clienteling Copilot</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 28 }}>
        {steps.map(([h, p], i) => (
          <React.Fragment key={h}>
            <div style={{ opacity: fadeIn(f, 110 + i * 45), background: i === 1 ? C.teal : '#1E293B', borderRadius: 22, padding: '34px 44px', minWidth: 380 }}>
              <div style={{ fontSize: 46, fontWeight: 700, color: '#F8FAFC' }}>{h}</div>
              <div style={{ fontSize: 30, color: i === 1 ? C.mint : C.muted, marginTop: 8 }}>{p}</div>
            </div>
            {i < 2 && <div style={{ opacity: fadeIn(f, 130 + i * 45), fontSize: 64, color: C.tealLight }}>→</div>}
          </React.Fragment>
        ))}
      </div>
      <div style={{ opacity: fadeIn(f, 330), fontSize: 44, color: C.mint }}>Nothing is uploaded. Nothing leaves the device.</div>
    </AbsoluteFill>
  );
};

/* ---------- S4: live demo (real prototype output) ---------- */
const S4: React.FC = () => {
  const f = useCurrentFrame();
  const demo = data.demo;
  const cmd = '$ python3 -m occ.cli bench/watch-1.m4a --llm gemma3:4b';
  const typed = cmd.slice(0, Math.floor(interpolate(f, [10, 70], [0, cmd.length], { extrapolateRight: 'clamp', extrapolateLeft: 'clamp' })));
  const rows: [string, string, boolean?][] = [
    ['client', demo.client],
    ['preferences', demo.preferences],
    ['wishlist', demo.wishlist],
    ['reminder', demo.reminder, true],
  ];
  return (
    <AbsoluteFill style={{ background: C.bg, fontFamily: FONT, padding: 100, gap: 32 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Eyebrow>Stage I prototype · running offline</Eyebrow>
        <div style={{ fontSize: 28, fontWeight: 700, color: '#B91C1C', background: '#FEF2F2', border: '2px solid #FECACA', borderRadius: 999, padding: '10px 24px' }}>Wi-Fi off</div>
      </div>
      <div style={{ display: 'flex', gap: 36, flex: 1 }}>
        <div style={{ flex: 1.1, background: C.ink, borderRadius: 22, padding: 40, fontFamily: MONO, fontSize: 28, color: '#E2E8F0', lineHeight: 1.6, overflow: 'hidden' }}>
          <div style={{ color: C.tealLight }}>{typed}</div>
          <div style={{ opacity: fadeIn(f, 90), color: C.muted, marginTop: 16 }}>[whisper.cpp] transcribing… {demo.stt_s}s</div>
          <div style={{ opacity: fadeIn(f, 110), marginTop: 10, fontFamily: FONT, fontSize: 32, color: '#F1F5F9' }}>{demo.transcript}</div>
          <div style={{ opacity: fadeIn(f, 260), color: C.muted, marginTop: 16 }}>[gemma3:4b] extracting with JSON schema… {demo.llm_s}s</div>
        </div>
        <div style={{ flex: 1, background: C.card, border: `1px solid ${C.line}`, borderRadius: 22, padding: 40, display: 'flex', flexDirection: 'column', gap: 24 }}>
          <div style={{ fontSize: 26, fontWeight: 700, color: C.teal, letterSpacing: 2, textTransform: 'uppercase' }}>Client record</div>
          {rows.map(([k, v, hl], i) => (
            <div key={k} style={{ opacity: fadeIn(f, 300 + i * 40), transform: `translateY(${rise(f, 300 + i * 40)}px)`, background: hl ? '#ECFDF5' : 'transparent', border: hl ? `2px solid ${C.teal}` : 'none', borderRadius: 14, padding: hl ? 18 : 0 }}>
              <div style={{ fontSize: 24, color: C.muted, textTransform: 'uppercase', letterSpacing: 2 }}>{k}</div>
              <div style={{ fontSize: 34, fontWeight: 600, color: C.ink, marginTop: 4 }}>{v}</div>
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ---------- S5: architecture ---------- */
const S5: React.FC = () => {
  const f = useCurrentFrame();
  const box = (title: string, body: string, start: number, accent = false) => (
    <div style={{ opacity: fadeIn(f, start), transform: `translateY(${rise(f, start)}px)`, background: accent ? '#ECFDF5' : C.card, border: `3px solid ${accent ? C.teal : '#CBD5E1'}`, borderRadius: 22, padding: 36 }}>
      <div style={{ fontSize: 40, fontWeight: 700, color: accent ? '#0F766E' : C.ink }}>{title}</div>
      <div style={{ fontSize: 28, color: accent ? '#134E4A' : C.slate, marginTop: 12, lineHeight: 1.45, whiteSpace: 'pre-line' }}>{body}</div>
    </div>
  );
  return (
    <AbsoluteFill style={{ background: C.bg, fontFamily: FONT, padding: 110, gap: 44 }}>
      <Eyebrow>Architecture</Eyebrow>
      <div style={{ fontSize: 68, fontWeight: 700, color: C.ink }}>The host orchestrates. The UGen300 does the AI.</div>
      <div style={{ display: 'flex', gap: 28, alignItems: 'center' }}>
        <div style={{ width: 330 }}>{box('Microphone', 'Counter PC or headset', 30)}</div>
        <div style={{ opacity: fadeIn(f, 60), fontSize: 64, color: C.muted }}>→</div>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 20 }}>
          {box('Host PC', 'Audio decode · validation · review UI · SQLite', 90)}
          {box('ASUS UGen300 · Hailo-10H', '① Whisper speech-to-text\n② Gemma 3 4B LLM, schema-constrained\nBoth resident in 8 GB on-module memory', 200, true)}
        </div>
        <div style={{ opacity: fadeIn(f, 330), fontSize: 64, color: C.muted }}>→</div>
        <div style={{ width: 330 }}>{box('Client record', 'Local database', 360)}</div>
      </div>
      <div style={{ opacity: fadeIn(f, 480), fontSize: 40, fontWeight: 700, color: C.teal }}>Network connection: not required.</div>
    </AbsoluteFill>
  );
};

/* ---------- S6: Stage I results ---------- */
const S6: React.FC = () => {
  const f = useCurrentFrame();
  const models = data.models as { name: string; accuracy: number; seconds: number }[];
  return (
    <AbsoluteFill style={{ background: C.bg, fontFamily: FONT, padding: 110, gap: 40 }}>
      <Eyebrow>Stage I results · laptop proxy, same model sizes</Eyebrow>
      <div style={{ fontSize: 68, fontWeight: 700, color: C.ink }}>8 scripted sales memos, 3 on-device models</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 30, marginTop: 10 }}>
        {models.map((m, i) => {
          const w = interpolate(f, [40 + i * 30, 90 + i * 30], [0, m.accuracy], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          return (
            <div key={m.name} style={{ display: 'flex', alignItems: 'center', gap: 28 }}>
              <div style={{ width: 300, fontSize: 36, fontWeight: 700, color: C.ink }}>{m.name}{m.name === 'Gemma 3 4B' ? ' ✓' : ''}</div>
              <div style={{ flex: 1, height: 64, background: '#E2E8F0', borderRadius: 12, overflow: 'hidden' }}>
                <div style={{ width: `${w * 100}%`, height: '100%', background: m.name === 'Gemma 3 4B' ? C.teal : '#94A3B8', borderRadius: 12 }} />
              </div>
              <div style={{ width: 380, fontSize: 34, color: C.slate }}>{Math.round(m.accuracy * 100)}% fields · {m.seconds}s</div>
            </div>
          );
        })}
      </div>
      <div style={{ opacity: fadeIn(f, 260), fontSize: 36, color: C.slate, lineHeight: 1.45 }}>{data.takeaway}</div>
    </AbsoluteFill>
  );
};

/* ---------- S7: Stage II + business ---------- */
const S7: React.FC = () => {
  const f = useCurrentFrame();
  const weeks = ['Port Whisper to Hailo-10H', 'Deploy Gemma 3 4B + schema', 'End-to-end · latency & power', 'Field test · repo · demo'];
  return (
    <AbsoluteFill style={{ background: C.bg, fontFamily: FONT, padding: 110, gap: 44 }}>
      <Eyebrow>Stage II · Nov 6 – Dec 4</Eyebrow>
      <div style={{ display: 'flex', gap: 22 }}>
        {weeks.map((w, i) => (
          <div key={w} style={{ flex: 1, opacity: fadeIn(f, 20 + i * 30), background: i === 0 ? C.teal : C.card, border: `1px solid ${C.line}`, borderRadius: 20, padding: 32 }}>
            <div style={{ fontSize: 28, fontWeight: 700, color: i === 0 ? C.mint : C.teal }}>WEEK {i + 1}</div>
            <div style={{ fontSize: 34, fontWeight: 600, color: i === 0 ? '#FFFFFF' : C.ink, marginTop: 10, lineHeight: 1.3 }}>{w}</div>
          </div>
        ))}
      </div>
      <div style={{ opacity: fadeIn(f, 330), background: C.ink, borderRadius: 24, padding: 48, display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div style={{ fontSize: 56, fontWeight: 700, color: '#F8FAFC' }}>The AI counter box</div>
        <div style={{ fontSize: 34, color: C.mint }}>ASUS mini PC + UGen300, preinstalled · per-seat licence</div>
        <div style={{ fontSize: 32, color: C.muted }}>Insurance agencies · luxury brands · car dealers · real estate</div>
      </div>
    </AbsoluteFill>
  );
};

/* ---------- S8: close ---------- */
const S8: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: `linear-gradient(135deg, ${C.ink}, #10302E)`, fontFamily: FONT, justifyContent: 'center', alignItems: 'center', gap: 28 }}>
      <div style={{ opacity: fadeIn(f), fontSize: 100, fontWeight: 700, color: '#F8FAFC' }}>Offline Clienteling Copilot</div>
      <div style={{ opacity: fadeIn(f, 20), fontSize: 48, color: C.tealLight }}>Private by design. Built for the counter.</div>
      <div style={{ opacity: fadeIn(f, 50), fontSize: 30, color: C.muted, marginTop: 30 }}>Team HueiHe · ASUS UGen AI League 2026 · Workplace AI · Battlefield Lightning</div>
    </AbsoluteFill>
  );
};

const SCENES: Record<SceneId, React.FC> = { s1: S1, s2: S2, s3: S3, s4: S4, s5: S5, s6: S6, s7: S7, s8: S8 };

const Pitch: React.FC = () => {
  let at = 0;
  return (
    <AbsoluteFill style={{ background: C.ink }}>
      {ORDER.map((id) => {
        const from = at;
        const d = dur(id);
        at += d;
        const Scene = SCENES[id];
        return (
          <Sequence key={id} from={from} durationInFrames={d}>
            <Scene />
            <Audio src={staticFile(`vo/${id}.wav`)} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

export const RemotionRoot: React.FC = () => (
  <Composition id="Pitch" component={Pitch} durationInFrames={ORDER.reduce((s, id) => s + dur(id), 0)} fps={FPS} width={1920} height={1080} />
);
