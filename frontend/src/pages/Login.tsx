import { useState, type FormEvent, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { PapelUsuario } from '../types';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { isDemoMode } from '../demo/demoData';

const demoProfiles = [
  { nome: 'Azul Linhas Aéreas', email: 'linhas.aereas@azul.com.br' },
  { nome: 'Azul Conecta', email: 'conecta@azul.com.br' },
  { nome: 'Azul Cargo Express', email: 'cargo@azul.com.br' },
  { nome: 'Azul Viagens', email: 'viagens@azul.com.br' },
  { nome: 'Azul Fidelidade', email: 'fidelidade@azul.com.br' },
  { nome: 'Azul TecOps', email: 'tecops@azul.com.br' },
  { nome: 'Marketing', email: 'marketing@azul.com.br' },
] as const;

const DEMO_PASSWORD = 'teste123';

export function Login() {
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [showSenha, setShowSenha] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, isAuthenticated, currentUser } = useAuth();
  const navigate = useNavigate();

  const handleUseProfile = (emailValue: string) => {
    setEmail(emailValue);
    setSenha(DEMO_PASSWORD);
    setError('');
  };

  // Demo mode: redirect directly to vertical portal
  useEffect(() => {
    if (isDemoMode()) {
      navigate('/vertical', { replace: true });
    }
  }, [navigate]);

  if (isAuthenticated && currentUser) {
    const redirect: Record<string, string> = {
      [PapelUsuario.VERTICAL]: '/vertical',
      [PapelUsuario.MARKETING]: '/marketing',
      [PapelUsuario.ADMIN]: '/marketing',
      [PapelUsuario.LIDERANCA]: '/lideranca',
    };
    navigate(redirect[currentUser.papel] || '/vertical', { replace: true });
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, senha);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || 'Erro ao fazer login');
      } else {
        setError('Erro de conexão com o servidor');
      }
    } finally {
      setLoading(false);
    }
  };

  // In demo mode, don't render the login page (redirect happens in useEffect)
  if (isDemoMode()) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-azul-800 via-azul-700 to-azul-900 flex items-start justify-center p-4 pt-20 pb-20">
      <div className="w-full max-w-4xl">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-white/10 backdrop-blur-sm mb-4">
            <span className="text-3xl font-bold text-white">F</span>
          </div>
          <h1 className="text-3xl font-bold text-white">Farol</h1>
          <p className="text-azul-200 mt-1">Inteligência estratégica para projetos da Azul</p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Acessar plataforma</h2>

          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-azul-500 focus:border-azul-500 outline-none"
                placeholder="seu@email.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Senha</label>
              <div className="relative">
                <input
                  type={showSenha ? 'text' : 'password'}
                  value={senha}
                  onChange={(e) => setSenha(e.target.value)}
                  required
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-azul-500 focus:border-azul-500 outline-none pr-10"
                  placeholder="Sua senha"
                />
                <button
                  type="button"
                  onClick={() => setShowSenha(!showSenha)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showSenha ? (
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            <Button type="submit" loading={loading} className="w-full">
              Entrar
            </Button>
          </form>

          <div className="mt-8 pt-8 border-t border-gray-100">
            <h3 className="text-sm font-semibold text-gray-700 text-center mb-2">Ambiente de demonstração</h3>
            <p className="text-sm text-gray-600 text-center mb-4">Selecione uma unidade para preencher as credenciais de demonstração.</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 max-h-96 overflow-y-auto">
              {demoProfiles.map((profile) => (
                <Card key={profile.email} className="p-4 hover:shadow-md transition-shadow cursor-pointer">
                  <div className="text-center">
                    <p className="font-semibold text-gray-900 text-sm">{profile.nome}</p>
                    <p className="text-xs text-gray-600 mt-1 break-all">{profile.email}</p>
                    <Button
                      variant="secondary"
                      className="w-full mt-3 whitespace-nowrap"
                      onClick={() => handleUseProfile(profile.email)}
                    >
                      Usar este perfil
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
            <p className="text-xs text-gray-500 text-center mt-4">Senha de demonstração para todos os perfis: {DEMO_PASSWORD}</p>
          </div>
        </div>
      </div>
    </div>
  );
}