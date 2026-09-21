/**
 * Tile art for the live-casino lobby.
 *
 * Drawn here as inline SVG rather than pulled off the web: hotlinked images break,
 * and the artwork on other exchanges is theirs, not ours. Each family gets its own
 * colours and motif so the lobby reads at a glance.
 */
const THEMES: Record<string, { from: string; to: string; motif: string }> = {
  teenpatti: { from: "#0f766e", to: "#065f46", motif: "cards" },
  poker: { from: "#1e3a8a", to: "#172554", motif: "cards" },
  card: { from: "#7c2d12", to: "#431407", motif: "cards" },
  dragontiger: { from: "#b91c1c", to: "#450a0a", motif: "dragon" },
  lucky7: { from: "#a16207", to: "#451a03", motif: "seven" },
  card32: { from: "#4c1d95", to: "#2e1065", motif: "cards" },
  baccarat: { from: "#1f2937", to: "#030712", motif: "chip" },
  cricket: { from: "#166534", to: "#052e16", motif: "ball" },
  race: { from: "#0369a1", to: "#082f49", motif: "chip" },
  worli: { from: "#9d174d", to: "#4c0519", motif: "chip" },
};

function motifPath(motif: string): string {
  switch (motif) {
    case "dragon":
      return `<path d='M150 78 l26 26 -26 26 -26 -26z' fill='#fff' opacity='.9'/>
              <circle cx='150' cy='104' r='9' fill='${"#fca5a5"}'/>`;
    case "seven":
      return `<text x='150' y='128' font-family='Georgia,serif' font-size='74' font-weight='bold'
                    fill='#fff' opacity='.92' text-anchor='middle'>7</text>`;
    case "ball":
      return `<circle cx='150' cy='104' r='30' fill='#dc2626'/>
              <path d='M120 104 h60' stroke='#fff' stroke-width='3' opacity='.8'/>`;
    case "chip":
      return `<circle cx='150' cy='104' r='32' fill='#fff' opacity='.92'/>
              <circle cx='150' cy='104' r='22' fill='none' stroke='#0f172a' stroke-width='6'/>`;
    default:
      return `<g opacity='.95'>
                <rect x='108' y='74' width='44' height='62' rx='6' fill='#fff' transform='rotate(-12 130 105)'/>
                <rect x='148' y='74' width='44' height='62' rx='6' fill='#fff' transform='rotate(10 170 105)'/>
                <text x='128' y='116' font-family='Georgia,serif' font-size='24' fill='#b91c1c'
                      transform='rotate(-12 130 105)'>A</text>
                <text x='168' y='116' font-family='Georgia,serif' font-size='24' fill='#0f172a'
                      transform='rotate(10 170 105)'>K</text>
              </g>`;
  }
}

/** A deterministic 300x200 tile for one game. */
export function casinoTileArt(name: string, category: string): string {
  const theme = THEMES[category] ?? THEMES.card;
  const label = name.length > 22 ? `${name.slice(0, 21)}…` : name;
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='300' height='200'>
    <defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>
      <stop offset='0' stop-color='${theme.from}'/><stop offset='1' stop-color='${theme.to}'/>
    </linearGradient></defs>
    <rect width='300' height='200' fill='url(#g)'/>
    <circle cx='40' cy='34' r='60' fill='#ffffff' opacity='.06'/>
    <circle cx='268' cy='176' r='70' fill='#000000' opacity='.12'/>
    ${motifPath(theme.motif)}
    <text x='150' y='176' font-family='Inter,system-ui,sans-serif' font-size='16' font-weight='700'
          fill='#ffffff' text-anchor='middle' opacity='.95'>${label
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")}</text>
  </svg>`;
  return `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svg)))}`;
}
