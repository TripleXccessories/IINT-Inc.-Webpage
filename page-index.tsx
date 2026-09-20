import { useEffect, useState } from "react";
import LoadingScreen, { IINT_SEQUENCE_MS } from "../components/iint-logo/loading-screen";

export function readFlag(name: string): boolean {
  if (typeof window === "undefined") return false;
  return new URLSearchParams(window.location.search).has(name);
}

/**
 * One page, three jobs, all driven by query flags:
 *
 *   (default)    the playground — every control on screen
 *   ?bare        no controls at all: the clean embed / recording surface
 *   ?letters     letter words on
 *   ?notext      right-hand text block off
 *   ?play        run the master fade-out instead of holding the final frame
 *   ?loop        replay forever (implies ?play)
 *   ?mute        start with the cue off
 *   ?nobadge     hide the "Made with Runable" badge (read in app.tsx)
 *   ?armed       hold on black until window.__iintStart() fires (frame-exact capture)
 */
function Index() {
  const bare = readFlag("bare");
  const loop = readFlag("loop");
  const play = readFlag("play") || loop;

  const [armed, setArmed] = useState(() => readFlag("armed"));

  const [runKey, setRunKey] = useState(1);
  const [labeled, setLabeled] = useState(() => readFlag("letters") || readFlag("labeled"));
  const [showTextBlock, setShowTextBlock] = useState(() => !readFlag("notext"));
  const [sound, setSound] = useState(() => !readFlag("mute"));

  // recording harness: the capture arms the page, then releases it on an exact frame
  useEffect(() => {
    if (!armed) return;
    (window as unknown as { __iintStart?: () => void }).__iintStart = () => setArmed(false);
    return () => {
      delete (window as unknown as { __iintStart?: () => void }).__iintStart;
    };
  }, [armed]);

  // looping embed: restart a beat after the fade-out lands
  useEffect(() => {
    if (!loop) return;
    const t = setTimeout(() => setRunKey((k) => k + 1), IINT_SEQUENCE_MS + 1400);
    return () => clearTimeout(t);
  }, [loop, runKey]);

  return (
    <div className="min-h-screen bg-[#01070c]">
      {!armed && (
        <LoadingScreen
          key={runKey}
          runKey={runKey}
          hold={!play}
          labeled={labeled}
          showTextBlock={showTextBlock}
          sound={sound}
        />
      )}

      {/* preview controls — not part of the logo itself */}
      {!bare && (
        <div className="fixed bottom-5 left-1/2 z-[60] flex -translate-x-1/2 flex-wrap items-center justify-center gap-2 rounded-full border border-[#0e3a34] bg-black/70 px-3 py-2 backdrop-blur">
          <button
            type="button"
            onClick={() => setRunKey((k) => k + 1)}
            className="rounded-full bg-[#00d4aa] px-4 py-1.5 text-xs font-medium tracking-widest text-black uppercase"
          >
            Replay 18.5s
          </button>
          <button
            type="button"
            onClick={() => {
              setLabeled((v) => !v);
              setRunKey((k) => k + 1);
            }}
            className={`rounded-full border px-3 py-1.5 text-xs tracking-widest uppercase ${
              labeled ? "border-[#00d4aa] text-[#00d4aa]" : "border-[#1d4a44] text-[#5f9c92]"
            }`}
          >
            Letter words
          </button>
          <button
            type="button"
            onClick={() => {
              setShowTextBlock((v) => !v);
              setRunKey((k) => k + 1);
            }}
            className={`rounded-full border px-3 py-1.5 text-xs tracking-widest uppercase ${
              showTextBlock ? "border-[#1d4a44] text-[#5f9c92]" : "border-[#00d4aa] text-[#00d4aa]"
            }`}
          >
            {showTextBlock ? "Hide text block" : "Text block hidden"}
          </button>
          <button
            type="button"
            onClick={() => setSound((v) => !v)}
            className={`rounded-full border px-3 py-1.5 text-xs tracking-widest uppercase ${
              sound ? "border-[#00d4aa] text-[#00d4aa]" : "border-[#1d4a44] text-[#5f9c92]"
            }`}
          >
            {sound ? "Sound on" : "Sound off"}
          </button>
        </div>
      )}
    </div>
  );
}

export default Index;
