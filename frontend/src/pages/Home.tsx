import { FormEvent, useEffect, useState } from 'react';
import api from '../api';

type Project = { id: number; name: string; vertical: string; owner: string; stage: string; status: string; score: number; updated: string };
type Dashboard = { summary: { active: number; approved: number; attention: number; risk: number }; projects: Project[] };
type Evaluation = { score: number; title: string; summary: string; strengths: string[]; alerts: string[]; next_step: string };

const statusLabel: Record<string, string> = { approved: 'No caminho', attention: 'Atenção', risk: 'Em risco' };

function Home() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [selected, setSelected] = useState<Project | null>(null);
  const [description, setDescription] = useState('Uma experiência que recomenda roteiros personalizados a partir do perfil, orçamento e preferências do viajante. O piloto será realizado com clientes recorrentes.');
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/api/demo/dashboard').then(({ data }) => setData(data)).catch(() => setError('Não foi possível acessar o backend. Rode ./start-demo.sh no terminal.'));
  }, []);

  async function evaluate(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setEvaluation(null);
    try {
      const response = await api.post('/api/demo/evaluate', { project_id: selected?.id ?? 1, description });
      setEvaluation(response.data);
    } catch {
      setError('A simulação falhou. Verifique se o backend está rodando.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">F</span><span>Farol</span></div>
        <nav>
          <a className="active" href="#dashboard">▦ <span>Visão geral</span></a>
          <a href="#projects">◇ <span>Projetos</span></a>
          <a href="#alerts">△ <span>Alertas</span><b>2</b></a>
          <a href="#history">◷ <span>Histórico</span></a>
        </nav>
        <div className="sidebar-bottom">
          <div className="simulation"><i /> Modo demonstração</div>
          <div className="profile"><div className="avatar">MC</div><div><strong>Marina Costa</strong><small>Vertical Viagens</small></div></div>
        </div>
      </aside>

      <main>
        <header><div><p>SEXTA-FEIRA, 17 DE JULHO</p><h1>Olá, Marina <span>👋</span></h1><small>Acompanhe seus projetos e tome decisões com mais segurança.</small></div><button className="primary" onClick={() => setSelected(data?.projects[0] ?? null)}>＋ Nova avaliação</button></header>

        {error && <div className="error">{error}</div>}
        <section className="metrics">
          {[
            ['Projetos ativos', data?.summary.active ?? '—', '↗ 2 este mês', 'blue'],
            ['No caminho', data?.summary.approved ?? '—', '58% do total', 'green'],
            ['Pedem atenção', data?.summary.attention ?? '—', 'Revisar esta semana', 'amber'],
            ['Em risco', data?.summary.risk ?? '—', 'Ação necessária', 'red'],
          ].map(([label, value, note, color]) => <article className={`metric ${color}`} key={label}><div className="metric-top"><span>{label}</span><i /></div><strong>{value}</strong><small>{note}</small></article>)}
        </section>

        <section className="content-grid" id="projects">
          <div className="panel projects-panel">
            <div className="panel-title"><div><h2>Projetos recentes</h2><p>Últimas avaliações e movimentações</p></div><button>Ver todos →</button></div>
            <div className="table-head"><span>PROJETO</span><span>ETAPA</span><span>FAROL</span><span>ATUALIZADO</span></div>
            {data?.projects.map(project => <button className="project-row" key={project.id} onClick={() => { setSelected(project); setEvaluation(null); }}>
              <span className="project-name"><i>{project.name.charAt(0)}</i><span><strong>{project.name}</strong><small>{project.vertical} · {project.owner}</small></span></span>
              <span className="stage">{project.stage}</span>
              <span className={`badge ${project.status}`}><i /> {statusLabel[project.status]} · {project.score}</span>
              <span className="updated">{project.updated} ›</span>
            </button>)}
          </div>
          <div className="panel action-panel">
            <div className="panel-title"><div><h2>Próximas ações</h2><p>Prioridades sugeridas pelo Farol</p></div></div>
            <div className="action"><span className="action-icon amber">!</span><div><strong>Revisar métricas do projeto</strong><p>Roteiros Inteligentes</p><small>Hoje</small></div></div>
            <div className="action"><span className="action-icon red">↑</span><div><strong>Responder alerta crítico</strong><p>Carteira Verde</p><small>Até amanhã</small></div></div>
            <div className="action"><span className="action-icon blue">✓</span><div><strong>Preparar checkpoint</strong><p>Clube de Benefícios</p><small>Em 3 dias</small></div></div>
          </div>
        </section>

        <section className="insight"><span>✦</span><div><strong>Insight da semana</strong><p>Projetos com métricas definidas na ideação avançaram <b>2,3× mais rápido</b> para o pré-lançamento.</p></div><button onClick={() => setSelected(data?.projects[0] ?? null)}>Avaliar projeto →</button></section>
      </main>

      {selected && <div className="modal-backdrop" onMouseDown={() => !loading && setSelected(null)}><div className="modal" onMouseDown={event => event.stopPropagation()}>
        <button className="close" onClick={() => setSelected(null)}>×</button>
        <div className="modal-label">✦ AVALIAÇÃO SIMULADA</div>
        <h2>{selected.name}</h2><p className="muted">Nenhuma IA externa será chamada. O resultado abaixo é fixo para a apresentação.</p>
        {!evaluation ? <form onSubmit={evaluate}><label>Descreva a proposta do projeto</label><textarea value={description} onChange={event => setDescription(event.target.value)} minLength={3} required /><button className="primary evaluate" disabled={loading}>{loading ? <><span className="spinner" /> Analisando proposta...</> : '✦ Simular avaliação'}</button></form> : <div className="result">
          <div className="score"><strong>{evaluation.score}</strong><span>/ 100<br/><b>Atenção</b></span></div>
          <h3>{evaluation.title}</h3><p>{evaluation.summary}</p>
          <div className="result-cols"><div><h4>✓ Pontos fortes</h4>{evaluation.strengths.map(item => <p key={item}>• {item}</p>)}</div><div><h4>! Alertas</h4>{evaluation.alerts.map(item => <p key={item}>• {item}</p>)}</div></div>
          <div className="next-step"><strong>Próximo passo sugerido</strong><p>{evaluation.next_step}</p></div>
          <button className="secondary" onClick={() => setSelected(null)}>Concluir</button>
        </div>}
      </div></div>}
    </div>
  );
}

export default Home;
