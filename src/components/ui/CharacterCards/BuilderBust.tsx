export default function BuilderBust({ color }: { color: string }) {
  return (
    <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Corpo */}
      <path d="M20 100 Q50 50 80 100" fill={color} stroke="#334155" strokeWidth="3" />
      {/* Rosto */}
      <circle cx="50" cy="55" r="18" fill={color} stroke="#334155" strokeWidth="3" />
      {/* Capacete de Obra */}
      <path d="M28 50 A 22 22 0 0 1 72 50" fill="#f8fafc" stroke="#334155" strokeWidth="3" />
      <line x1="22" y1="50" x2="78" y2="50" stroke="#334155" strokeWidth="4" strokeLinecap="round" />
    </svg>
  );
}