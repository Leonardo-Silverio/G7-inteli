import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import { PageHeader } from '../components/PageHeader';
import { Card, CardBody, CardHeader } from '../components/Card';
import { Button } from '../components/Button';
import { ErrorAlert } from '../components/ErrorAlert';
import { isDemoMode } from '../demo/demoData';
import type { ProjetoResponse } from '../types';

export function NovoProjeto() {
  const navigate = useNavigate();
  const [titulo, setTitulo] = useState('');
  const [descricao, setDescricao] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [demoMessage, setDemoMessage] = useState('');

  const demoMode = isDemoMode();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setDemoMessage('');
    if (!titulo.trim()) {
      setError('O título é obrigatório');
      return;
    }
    if (demoMode) {
      setDemoMessage('Modo demonstração: esta ação não altera dados reais.');
      return;
    }
    setLoading(true);
    try {
      const res = await api.post<ProjetoResponse>('/projetos', {
        titulo: titulo.trim(),
        descricao: descricao.trim() || null,
      });
      navigate(`/projetos/${res.data.id}`);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || 'Erro ao criar projeto');
      } else {
        setError('Erro de conexão com o servidor');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <PageHeader
        title="Novo Projeto"
        subtitle="Preencha as informações para criar um novo projeto"
      />

      <Card>
        <CardHeader><h3 className="font-semibold text-gray-900">Informações do Projeto</h3></CardHeader>
        <CardBody>
          {error && <div className="mb-4"><ErrorAlert message={error} /></div>}
          {demoMessage && (
            <div className="mb-4 bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-700">
              {demoMessage}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Título <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={titulo}
                onChange={(e) => setTitulo(e.target.value)}
                required
                maxLength={200}
                className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-azul-500 focus:border-azul-500 outline-none"
                placeholder="Nome do projeto"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Descrição</label>
              <textarea
                value={descricao}
                onChange={(e) => setDescricao(e.target.value)}
                maxLength={5000}
                rows={4}
                className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-azul-500 focus:border-azul-500 outline-none resize-none"
                placeholder="Descreva o projeto (opcional)"
              />
            </div>

            <div className="flex items-center gap-3 pt-2">
              {!demoMode && (
                <Button type="submit" loading={loading}>Criar Projeto</Button>
              )}
              <Button type="button" variant="secondary" onClick={() => navigate('/projetos')}>
                Cancelar
              </Button>
              {demoMode && (
                <div className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3">
                  Modo demonstração: ações de escrita desabilitadas.
                </div>
              )}
            </div>
          </form>
        </CardBody>
      </Card>
    </div>
  );
}
