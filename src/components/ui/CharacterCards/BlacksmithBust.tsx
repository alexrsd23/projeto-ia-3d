export default function BlacksmithBust({ color }: { color: string }) {
  return (
    <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Martelo de Forja ao Fundo */}
      <rect x="70" y="20" width="8" height="60" rx="4" fill="#451a03" transform="rotate(15 70 20)" />
      <rect x="62" y="15" width="24" height="15" rx="2" fill="#334155" transform="rotate(15 62 15)" />
      
      {/* Corpo */}
      <path d="M20 100 Q50 50 80 100" fill={color} stroke="#334155" strokeWidth="3" />
      
      {/* Avental de Proteção (Couro Escuro) */}
      <path d="M35 70 L65 70 L60 100 L40 100 Z" fill="#2d3748" stroke="#1a202c" strokeWidth="1" />
      
      {/* Rosto */}
      <circle cx="50" cy="55" r="18" fill={color} stroke="#334155" strokeWidth="3" />
      
      {/* Ícone de Bigorna no Peito */}
      <path d="M42 80 H58 L56 88 H44 Z" fill="#94a3b8" />
      <rect x="40" y="78" width="20" height="3" fill="#94a3b8" />
    </svg>
  );
}