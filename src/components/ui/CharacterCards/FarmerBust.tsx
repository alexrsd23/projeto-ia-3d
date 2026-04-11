export default function FarmerBust({ color }: { color: string }) {
  return (
    <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Corpo */}
      <path d="M20 100 Q50 50 80 100" fill={color} stroke="#334155" strokeWidth="3" />
      {/* Rosto */}
      <circle cx="50" cy="55" r="18" fill={color} stroke="#334155" strokeWidth="3" />
      {/* Chapéu de Palha (Aba e Topo) */}
      <ellipse cx="50" cy="40" rx="35" ry="8" fill="#fef08a" stroke="#334155" strokeWidth="3" />
      <path d="M30 40 Q50 10 70 40" fill="#fde047" stroke="#334155" strokeWidth="3" />
    </svg>
  );
}