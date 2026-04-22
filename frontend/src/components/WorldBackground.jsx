const AMBIENT_PIXELS = [
  { x: '12%', y: '18%', dur: '14s', delay: '0s' },
  { x: '28%', y: '36%', dur: '18s', delay: '1.8s' },
  { x: '44%', y: '22%', dur: '16s', delay: '0.9s' },
  { x: '66%', y: '28%', dur: '20s', delay: '2.7s' },
  { x: '82%', y: '40%', dur: '24s', delay: '3.4s' },
  { x: '52%', y: '64%', dur: '22s', delay: '4.2s' },
  { x: '22%', y: '70%', dur: '21s', delay: '2.3s' },
]

function AmbientPixel({ x, y, dur, delay }) {
  return (
    <span
      className="ambient-pixel"
      aria-hidden
      style={{ left: x, top: y, '--dur': dur, '--delay': delay }}
    />
  )
}

export default function WorldBackground() {
  return (
    <div className="world-background" aria-hidden>
      <div className="world-gradient" />
      <div className="world-grid" />
      <div className="world-mesh" />
      <div className="world-noise" />
      <div className="world-scanlines" />
      <div className="world-crt-curve" />
      <div className="world-flicker" />
      <div className="world-particles">
        {AMBIENT_PIXELS.map((pixel, i) => <AmbientPixel key={i} {...pixel} />)}
      </div>
    </div>
  )
}
