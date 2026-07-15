import { useEffect, useState } from 'react';
import api from '../api';

function Home() {
  const [health, setHealth] = useState<string>('');

  useEffect(() => {
    api
      .get('/api/health')
      .then((res) => setHealth(res.data.status))
      .catch(() => setHealth('offline'));
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-900 text-zinc-100">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Farol</h1>
        <p className="text-zinc-400">Backend status: {health}</p>
      </div>
    </div>
  );
}

export default Home;
