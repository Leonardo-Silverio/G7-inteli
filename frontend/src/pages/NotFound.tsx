import { Link } from 'react-router-dom';

export function NotFound() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-azul-600 mb-4">404</h1>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Página não encontrada</h2>
        <p className="text-sm text-gray-500 mb-6">A página que você procura não existe ou foi removida.</p>
        <Link
          to="/"
          className="inline-flex items-center px-4 py-2 bg-azul-600 text-white font-medium rounded-lg hover:bg-azul-700 transition-colors"
        >
          Voltar ao início
        </Link>
      </div>
    </div>
  );
}
