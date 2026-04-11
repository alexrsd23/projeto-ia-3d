export default function WoodcutterBust({ color }: { color: string }) {
  return (
    <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Cabo do machado nas costas */}
      <line x1="75" y1="90" x2="85" y2="30" stroke="#78350f" strokeWidth="6" strokeLinecap="round" />
      {/* Lâmina do machado */}
      <path d="M85 45 Q100 40 95 60 Q80 55 83 40" fill="#cbd5e1" stroke="#334155" strokeWidth="2" />
      {/* Corpo */}
      <path d="M20 100 Q50 50 80 100" fill={color} stroke="#334155" strokeWidth="3" />
      {/* Rosto */}
      <circle cx="50" cy="55" r="18" fill={color} stroke="#334155" strokeWidth="3" />
    </svg>
  );
}