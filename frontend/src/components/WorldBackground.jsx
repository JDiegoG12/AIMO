import React from 'react'

const SPARKLES =[
  { x:'15%', y:'12%', dur:'3.2s', delay:'0s'   },
  { x:'30%', y:'6%',  dur:'4.1s', delay:'0.8s' },
  { x:'55%', y:'9%',  dur:'2.8s', delay:'1.5s' },
  { x:'72%', y:'5%',  dur:'3.7s', delay:'0.3s' },
  { x:'85%', y:'18%', dur:'4.5s', delay:'2.1s' },
]

function SparkleIcon({ x, y, dur, delay }) {
  return (
    <span
      className="sparkle"
      aria-hidden
      style={{ left: x, top: y, '--dur': dur, '--delay': delay }}
    >✦</span>
  )
}

function PixelCloud({ top, speed, delay, scale, opacity }) {
  return (
    <svg
      className="pixel-cloud"
      style={{ top, animationDuration: speed, animationDelay: delay, transform: `scale(${scale})`, opacity }}
      viewBox="0 0 64 32"
      xmlns="http://www.w3.org/2000/svg"
      shapeRendering="crispEdges"
      aria-hidden
    >
      <rect x="16" y="8" width="32" height="8" fill="#ffffff" />
      <rect x="8" y="16" width="48" height="8" fill="#ffffff" />
      <rect x="24" y="24" width="16" height="8" fill="#ffffff" />
    </svg>
  )
}

// NUEVO: Componente generador de Flores Pixeladas
function PixelFlower({ left, bottom, color1, color2, scale = 1, flip = false }) {
  return (
    <svg
      style={{ position: 'absolute', left, bottom, transform: `scale(${scale}) ${flip ? 'scaleX(-1)' : ''}`, zIndex: 3 }}
      width="16" height="24" viewBox="0 0 16 24" xmlns="http://www.w3.org/2000/svg" shapeRendering="crispEdges" aria-hidden
    >
      {/* Tallo verde oscuro */}
      <rect x="6" y="12" width="4" height="12" fill="#27a849"/>
      {/* Hojas */}
      <rect x="2" y="16" width="4" height="4" fill="#1e8c3a"/>
      <rect x="10" y="14" width="4" height="4" fill="#1e8c3a"/>
      {/* Pétalos */}
      <rect x="6" y="0" width="4" height="4" fill={color1}/>
      <rect x="2" y="4" width="4" height="4" fill={color1}/>
      <rect x="10" y="4" width="4" height="4" fill={color1}/>
      <rect x="6" y="8" width="4" height="4" fill={color1}/>
      {/* Centro de la flor */}
      <rect x="6" y="4" width="4" height="4" fill={color2}/>
    </svg>
  )
}

export default function WorldBackground() {
  return (
    <>
      {/* ☀️ Sol animado */}
      <div className="sun-bg" aria-hidden />

      {/* ☁️ Nubes en movimiento */}
      <PixelCloud top="12%" speed="45s" delay="0s" scale="1.5" opacity="0.8" />
      <PixelCloud top="25%" speed="60s" delay="-20s" scale="1.2" opacity="0.6" />
      <PixelCloud top="18%" speed="35s" delay="-10s" scale="2" opacity="0.9" />
      <PixelCloud top="35%" speed="70s" delay="-40s" scale="0.8" opacity="0.5" />

      {/* ✨ Estrellitas mágicas */}
      <div className="sparkles" aria-hidden>
        {SPARKLES.map((s, i) => <SparkleIcon key={i} {...s} />)}
      </div>

      {/* ⛰️ Montañas lejanas */}
      <svg className="pixel-hills" viewBox="0 0 200 50" preserveAspectRatio="none" shapeRendering="crispEdges" aria-hidden>
         <path d="M0,50 L0,30 L10,30 L10,25 L20,25 L20,20 L30,20 L30,15 L40,15 L40,20 L50,20 L50,25 L60,25 L60,35 L80,35 L80,20 L90,20 L90,10 L100,10 L100,15 L110,15 L110,25 L120,25 L120,30 L140,30 L140,40 L160,40 L160,30 L180,30 L180,40 L200,40 L200,50 Z" fill="#71c771" opacity="0.6"/>
         <path d="M0,50 L0,40 L15,40 L15,35 L30,35 L30,25 L45,25 L45,30 L60,30 L60,45 L85,45 L85,30 L105,30 L105,20 L125,20 L125,35 L145,35 L145,45 L170,45 L170,35 L200,35 L200,50 Z" fill="#58a858" opacity="0.8"/>
      </svg>

      {/* 🌳 Árbol Pixelado */}
      <svg className="pixel-tree" viewBox="0 0 70 110" xmlns="http://www.w3.org/2000/svg" shapeRendering="crispEdges" aria-hidden>
        <rect x="27" y="72" width="16" height="38" fill="#5d3a1a"/>
        <rect x="31" y="72" width="6"  height="38" fill="#7c4f25"/>
        <rect x="10" y="50" width="50" height="28" fill="#1a6b2f"/>
        <rect x="4"  y="38" width="62" height="22" fill="#1e8c3a"/>
        <rect x="10" y="26" width="50" height="18" fill="#27a849"/>
        <rect x="18" y="14" width="34" height="16" fill="#34c05a"/>
        <rect x="24" y="4"  width="22" height="14" fill="#48d66e"/>
        <rect x="8"  y="52" width="6" height="6" fill="#ff7da8"/>
        <rect x="36" y="40" width="6" height="6" fill="#ff4d8b"/>
        <rect x="56" y="48" width="6" height="6" fill="#ff7da8"/>
        <rect x="22" y="30" width="4" height="4" fill="#ff2670"/>
      </svg>

      {/* 🍄 Tubería Pixelada */}
      <svg className="pixel-pipe" viewBox="0 0 64 130" xmlns="http://www.w3.org/2000/svg" shapeRendering="crispEdges" aria-hidden>
        <rect x="8"  y="28" width="48" height="102" fill="#6528b8"/>
        <rect x="8"  y="28" width="12" height="102" fill="#843bed"/>
        <rect x="50" y="28" width="6"  height="102" fill="#4b1d8a"/>
        <rect x="0"  y="14" width="64" height="18"  fill="#843bed"/>
        <rect x="0"  y="14" width="16" height="18"  fill="#a868f0"/>
        <rect x="52" y="14" width="12" height="18"  fill="#6528b8"/>
        <rect x="0"  y="10" width="64" height="6"   fill="#4b1d8a"/>
      </svg>

      {/* 🌷 FLORES ESPARCIDAS POR EL PASTO */}
      <PixelFlower left="12%" bottom="74px" color1="#ff7da8" color2="#ffde59" scale="1.2" />
      <PixelFlower left="24%" bottom="72px" color1="#ffffff" color2="#ffde59" scale="0.9" flip />
      <PixelFlower left="42%" bottom="75px" color1="#5de0e6" color2="#ffffff" scale="1.1" />
      <PixelFlower left="68%" bottom="73px" color1="#ffde59" color2="#ff7da8" scale="1" flip />
      <PixelFlower left="85%" bottom="76px" color1="#ff7da8" color2="#ffffff" scale="1.3" />

      {/* 🟩 Suelo de Pasto y Tierra */}
      <div className="ground" aria-hidden />
    </>
  )
}