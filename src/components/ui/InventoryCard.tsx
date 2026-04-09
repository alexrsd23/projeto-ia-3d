import React from 'react';

interface InventoryCardProps {
  inventoryJSON?: string;
}

export default function InventoryCard({ inventoryJSON }: InventoryCardProps) {
  // Parse seguro e isolado do JSON da mochila
  let inventory = { potatoes: 0, seeds: 0 };
  try {
    if (inventoryJSON) {
      inventory = JSON.parse(inventoryJSON);
    }
  } catch (e) {
    console.error("Erro ao processar a mochila do fazendeiro:", e);
  }

  return (
    <div style={{ background: '#fffbeb', padding: '12px', borderRadius: '8px', marginBottom: '15px', border: '1px solid #fde68a' }}>
      <h4 style={{ fontSize: '12px', color: '#b45309', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        🎒 Mochila (Reserva)
      </h4>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: '#92400e', fontWeight: 600 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span>🥔 Batatas:</span>
          <span style={{ background: '#fef3c7', padding: '2px 6px', borderRadius: '4px' }}>
            {inventory.potatoes || 0} / 4
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span>🌱 Sementes:</span>
          <span style={{ background: '#fef3c7', padding: '2px 6px', borderRadius: '4px' }}>
            {inventory.seeds || 0} / 4
          </span>
        </div>
      </div>
    </div>
  );
}