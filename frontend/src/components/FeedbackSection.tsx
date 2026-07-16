import { Card, CardBody, CardHeader } from './Card';
import type { FeedbackItem } from '../types';
import { FeedbackEstruturado } from '../types';

interface FeedbackSectionProps {
  feedback: FeedbackEstruturado;
}

function FeedbackItemCard({ item, icon, color }: { item: FeedbackItem; icon: string; color: string }) {
  return (
    <div className={`border-l-4 ${color} bg-gray-50 rounded-r-lg p-4`}>
      <div className="flex items-start gap-2">
        <span className="text-lg">{icon}</span>
        <div>
          <h4 className="font-medium text-gray-900">{item.titulo}</h4>
          <p className="mt-1 text-sm text-gray-600">{item.descricao}</p>
          {item.evidencias.length > 0 && (
            <ul className="mt-2 space-y-1">
              {item.evidencias.map((ev, i) => (
                <li key={i} className="text-xs text-gray-500 flex items-start gap-1">
                  <span className="mt-0.5">•</span> {ev}
                </li>
              ))}
            </ul>
          )}
          {item.prioridade && (
            <span className={`mt-2 inline-block text-xs font-medium px-2 py-0.5 rounded ${
              item.prioridade === 'ALTA' ? 'bg-red-100 text-red-700' :
              item.prioridade === 'MEDIA' ? 'bg-amber-100 text-amber-700' :
              'bg-blue-100 text-blue-700'
            }`}>
              {item.prioridade}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export function FeedbackSection({ feedback }: FeedbackSectionProps) {
  if (!feedback) return null;
  return (
    <div className="space-y-6">
      {feedback.justificativa_classificacao && (
        <Card>
          <CardBody>
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">Justificativa da Classificação</h3>
            <p className="text-gray-800">{feedback.justificativa_classificacao}</p>
          </CardBody>
        </Card>
      )}

      {feedback.pontos_fortes.length > 0 && (
        <Card>
          <CardHeader><h3 className="font-semibold text-gray-900">Pontos Fortes</h3></CardHeader>
          <CardBody className="space-y-3">
            {feedback.pontos_fortes.map((item, i) => (
              <FeedbackItemCard key={i} item={item} icon="✅" color="border-emerald-400" />
            ))}
          </CardBody>
        </Card>
      )}

      {feedback.oportunidades_melhoria.length > 0 && (
        <Card>
          <CardHeader><h3 className="font-semibold text-gray-900">Oportunidades de Melhoria</h3></CardHeader>
          <CardBody className="space-y-3">
            {feedback.oportunidades_melhoria.map((item, i) => (
              <FeedbackItemCard key={i} item={item} icon="🔧" color="border-amber-400" />
            ))}
          </CardBody>
        </Card>
      )}

      {feedback.recomendacoes_praticas.length > 0 && (
        <Card>
          <CardHeader><h3 className="font-semibold text-gray-900">Recomendações Práticas</h3></CardHeader>
          <CardBody className="space-y-3">
            {feedback.recomendacoes_praticas.map((item, i) => (
              <FeedbackItemCard key={i} item={item} icon="💡" color="border-blue-400" />
            ))}
          </CardBody>
        </Card>
      )}

      {feedback.proximos_passos.length > 0 && (
        <Card>
          <CardHeader><h3 className="font-semibold text-gray-900">Próximos Passos</h3></CardHeader>
          <CardBody>
            <ul className="space-y-2">
              {feedback.proximos_passos.map((passo, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                  <span className="text-azul-500 mt-0.5">→</span>
                  {passo}
                </li>
              ))}
            </ul>
          </CardBody>
        </Card>
      )}

      {feedback.riscos_principais.length > 0 && (
        <Card>
          <CardHeader><h3 className="font-semibold text-gray-900">Riscos Principais</h3></CardHeader>
          <CardBody className="space-y-3">
            {feedback.riscos_principais.map((item, i) => (
              <FeedbackItemCard key={i} item={item} icon="⚠️" color="border-red-400" />
            ))}
          </CardBody>
        </Card>
      )}
    </div>
  );
}
