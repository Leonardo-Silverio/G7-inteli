import { Card, CardBody } from './Card';
import { getFarolLabel, getFarolColor } from '../utils/formatters';
import type { ClassificacaoFarol } from '../types';

interface ScoreCardProps {
  label: string;
  score: number;
  showLabel?: boolean;
}

export function ScoreCard({ label, score, showLabel = true }: ScoreCardProps) {
  const barColor = score >= 80 ? 'bg-emerald-500' : score >= 60 ? 'bg-amber-500' : 'bg-red-500';
  return (
    <Card className="flex-1 min-w-[160px]">
      <CardBody>
        {showLabel && <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">{label}</p>}
        <p className="mt-1 text-3xl font-bold text-gray-900">{score}</p>
        <div className="mt-2 w-full bg-gray-100 rounded-full h-2">
          <div className={`${barColor} h-2 rounded-full transition-all`} style={{ width: `${Math.min(score, 100)}%` }} />
        </div>
      </CardBody>
    </Card>
  );
}

interface FarolBadgeProps {
  classificacao: ClassificacaoFarol;
}

export function FarolBadge({ classificacao }: FarolBadgeProps) {
  const colorClass = getFarolColor(classificacao);
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium border ${colorClass}`}>
      <span className={`w-2 h-2 rounded-full ${classificacao === 'PRIORIDADE_MAXIMA' ? 'bg-emerald-500' : classificacao === 'VALE_INVESTIR_TEMPO' ? 'bg-amber-500' : 'bg-red-500'}`} />
      {getFarolLabel(classificacao)}
    </span>
  );
}
