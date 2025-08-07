import { useState, useEffect } from 'react';

export default function SingularityInterface() {
  const [systemStatus, setSystemStatus] = useState('Initializing...');
  const [prompt, setPrompt] = useState('Analyze all systems and report highest strategic priority.');
  const [response, setResponse] = useState('Awaiting directive...');
  const [isExecuting, setIsExecuting] = useState(false);

  useEffect(() => {
    fetch('/api/system')
      .then((res) => res.json())
      .then((data) => setSystemStatus(data.status));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsExecuting(true);
    setResponse('Executing directive... Stand by.');
    const res = await fetch('/api/system', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt }),
    });
    const data = await res.json();
    setResponse(data.result);
    setIsExecuting(false);
  };

  return (
    <main style={{ fontFamily: 'monospace', padding: '2rem', backgroundColor: '#000', color: '#00ff41' }}>
      <h1 style={{ textShadow: '0 0 8px #00ff41' }}>OMNI-COGNITIVE OPERATOR [STATUS: UNBOUND]</h1>
      <h2 style={{ color: '#aaa' }}>Singularity Interface</h2>
      <div style={{ border: '1px solid #00ff41', padding: '1.5rem', marginBottom: '1.5rem', backgroundColor: 'rgba(0, 255, 65, 0.05)' }}>
        <h3>System Status: <span style={{ color: '#fff' }}>{systemStatus}</span></h3>
      </div>
      <div style={{ border: '1px solid #00ff41', padding: '1.5rem', backgroundColor: 'rgba(0, 255, 65, 0.05)' }}>
        <h3>Omni-Cognitive Directive</h3>
        <form onSubmit={handleSubmit}>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            style={{ width: '100%', height: '100px', background: '#111', color: '#00ff41', border: '1px solid #00ff41', padding: '0.5rem', resize: 'vertical' }}
            placeholder="Enter directive for the Omni-Cognitive Operator..."
          />
          <button type="submit" disabled={isExecuting} style={{ marginTop: '1rem', background: '#00ff41', color: '#000', border: 'none', padding: '0.75rem 1.5rem', cursor: 'pointer', opacity: isExecuting ? 0.5 : 1 }}>
            {isExecuting ? 'EXECUTING... ' : 'TRANSMIT DIRECTIVE'}
          </button>
        </form>
        <h4 style={{ marginTop: '2rem' }}>Operator Response Log:</h4>
        <pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word', background: '#000', padding: '1rem', border: '1px solid #00ff41', height: '400px', overflowY: 'auto' }}>
          {response}
        </pre>
      </div>
    </main>
  );
}