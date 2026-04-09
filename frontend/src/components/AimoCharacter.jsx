import { useState, useEffect } from 'react'

/**
 * AimoCharacter
 * Tries to load /aimo.png from the public folder.
 * Falls back to the inline SVG if the image fails to load.
 *
 * To use your PNG: copy it to  frontend/public/aimo.png
 */
function AimoSVG() {
  return (
    <svg
      className="aimo-img"
      width="200" height="300"
      viewBox="0 0 192 288"
      xmlns="http://www.w3.org/2000/svg"
      shapeRendering="crispEdges"
      aria-label="AIMO"
    >
      {/* Antenna */}
      <rect x="88"  y="10" width="16" height="28" fill="#111827"/>
      <rect x="76"  y="0"  width="40" height="16" fill="#5de0e6"/>
      <rect x="80"  y="8"  width="32" height="8"  fill="#38bdf8"/>
      <rect x="84"  y="14" width="24" height="4"  fill="#0ea5e9"/>
      {/* Star on antenna */}
      <rect x="84"  y="0"  width="4"  height="4"  fill="#fde68a"/>
      <rect x="96"  y="0"  width="4"  height="4"  fill="#fde68a"/>
      <rect x="80"  y="4"  width="32" height="4"  fill="#fbbf24"/>

      {/* Head */}
      <rect x="20"  y="38" width="152" height="116" fill="#7bc950"/>
      <rect x="28"  y="32" width="136" height="8"   fill="#7bc950"/>
      <rect x="36"  y="27" width="120" height="7"   fill="#7bc950"/>
      {/* head shine */}
      <rect x="28"  y="42" width="22"  height="40"  fill="#a5e071" fillOpacity=".45"/>
      <rect x="36"  y="30" width="40"  height="10"  fill="#a5e071" fillOpacity=".3"/>
      {/* head shadow */}
      <rect x="146" y="50" width="18"  height="92"  fill="#5a9a36" fillOpacity=".28"/>

      {/* Earpices */}
      <rect x="0"   y="62" width="28"  height="56" fill="#5de0e6"/>
      <rect x="4"   y="70" width="20"  height="40" fill="#0ea5e9"/>
      <rect x="8"   y="78" width="12"  height="24" fill="#0284c7"/>
      <rect x="164" y="62" width="28"  height="56" fill="#5de0e6"/>
      <rect x="168" y="70" width="20"  height="40" fill="#0ea5e9"/>
      <rect x="172" y="78" width="12"  height="24" fill="#0284c7"/>

      {/* Left eye */}
      <rect x="30"  y="60" width="56"  height="58" fill="#111827"/>
      <rect x="38"  y="68" width="28"  height="28" fill="white" className="eye-white left-eye"/>
      <rect x="46"  y="72" width="12"  height="12" fill="#111827"/>
      <rect x="54"  y="70" width="6"   height="6"  fill="white"/>
      {/* Right eye */}
      <rect x="106" y="60" width="56"  height="58" fill="#111827"/>
      <rect x="114" y="68" width="28"  height="28" fill="white" className="eye-white right-eye"/>
      <rect x="122" y="72" width="12"  height="12" fill="#111827"/>
      <rect x="130" y="70" width="6"   height="6"  fill="white"/>

      {/* Cheeks */}
      <rect x="20"  y="102" width="28" height="12" fill="#f87171" fillOpacity=".7"/>
      <rect x="144" y="102" width="28" height="12" fill="#f87171" fillOpacity=".7"/>

      {/* Smile */}
      <rect x="66"  y="122" width="60" height="8"  fill="#111827"/>
      <rect x="66"  y="114" width="8"  height="16" fill="#111827"/>
      <rect x="118" y="114" width="8"  height="16" fill="#111827"/>

      {/* Neck */}
      <rect x="72"  y="154" width="48" height="10" fill="#6b7280"/>

      {/* Body */}
      <rect x="34"  y="162" width="124" height="76" fill="#6b7280"/>
      <rect x="34"  y="162" width="18"  height="68" fill="#9ca3af" fillOpacity=".22"/>
      <rect x="140" y="170" width="18"  height="60" fill="#374151" fillOpacity=".32"/>
      <rect x="34"  y="230" width="124" height="8"  fill="#4b5563"/>

      {/* Screen */}
      <rect x="54"  y="174" width="84"  height="50" fill="#374151"/>
      <rect x="58"  y="178" width="76"  height="42" fill="#1e293b"/>
      <rect x="66"  y="186" width="60"  height="8"  fill="#5de0e6" fillOpacity=".9" className="screen-glow"/>
      <rect x="66"  y="198" width="44"  height="6"  fill="#5de0e6" fillOpacity=".5"/>
      <rect x="66"  y="208" width="28"  height="5"  fill="#5de0e6" fillOpacity=".25"/>

      {/* Left arm (waving) */}
      <rect x="2"   y="132" width="36"  height="22" fill="#7bc950"/>
      <rect x="0"   y="110" width="28"  height="30" fill="#7bc950"/>
      <rect x="0"   y="102" width="14"  height="16" fill="#7bc950"/>
      <rect x="12"  y="98"  width="10"  height="20" fill="#7bc950"/>
      <rect x="2"   y="152" width="32"  height="14" fill="#7bc950"/>

      {/* Right arm */}
      <rect x="154" y="168" width="36"  height="22" fill="#7bc950"/>
      <rect x="160" y="186" width="28"  height="28" fill="#7bc950"/>

      {/* Legs */}
      <rect x="54"  y="238" width="34"  height="26" fill="#7bc950"/>
      <rect x="104" y="238" width="34"  height="26" fill="#7bc950"/>

      {/* Shoes */}
      <rect x="42"  y="252" width="54"  height="20" fill="#5de0e6"/>
      <rect x="42"  y="264" width="54"  height="8"  fill="#0ea5e9"/>
      <rect x="38"  y="260" width="8"   height="12" fill="#5de0e6"/>
      <rect x="100" y="252" width="54"  height="20" fill="#5de0e6"/>
      <rect x="100" y="264" width="54"  height="8"  fill="#0ea5e9"/>
      <rect x="150" y="260" width="8"   height="12" fill="#5de0e6"/>
    </svg>
  )
}

export default function AimoCharacter({ phase }) {
  const [imgFailed, setImgFailed] = useState(false)

  // 1. Elegimos qué imagen mostrar según la fase actual del juego
  let currentImage = '/aimo.png'; // Imagen por defecto (esperando/intro)

  if (phase === 'loading') {
    currentImage = '/aimo-thinking.png'; // Imagen cuando está pensando
  } else if (phase === 'responding') {
    currentImage = '/aimo-talking.png';  // Imagen cuando está respondiendo
  }

  // 2. Si la fase cambia, reseteamos el error de imagen por si acaso
  useEffect(() => {
    setImgFailed(false)
  }, [currentImage])

  return (
    <>
      {!imgFailed ? (
        <img
          className="aimo-img"
          src={currentImage}
          alt={`AIMO - ${phase}`}
          onError={() => setImgFailed(true)}
          draggable={false}
        />
      ) : (
        // Si no encuentra alguna de las imágenes PNG, mostrará el SVG de respaldo
        <AimoSVG />
      )}
    </>
  )
}