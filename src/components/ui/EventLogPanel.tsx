import type { SimulationEvent } from '../../types';

interface EventLogProps {
  events: SimulationEvent[];
}

export default function EventLogPanel({ events }: EventLogProps) {
  return (
    <div className="event-log-panel">
      <h3>Terminal de Telemetria</h3>
      <div className="log-container">
        {events.length === 0 && <p style={{ color: '#7f8c8d' }}>Aguardando eventos...</p>}
        {events.map((evt) => (
          <div key={evt.id} className={`log-entry ${evt.level.toLowerCase()}`}>
            <span className="log-time">{new Date().toLocaleTimeString()}</span>
            <span className="log-message">{evt.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}