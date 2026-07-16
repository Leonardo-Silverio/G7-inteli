from uuid import UUID
from datetime import datetime, timezone
from pydantic import ValidationError
import logging

from app.models.enums import PapelUsuario, StatusCheckpoint, TipoCheckpoint
from app.models.checkpoint import Checkpoint
from app.models.anexo_checkpoint import AnexoCheckpoint
from app.models.projeto import Projeto
from app.repositories.checkpoint_repository import CheckpointRepository
from app.repositories.projeto_repository import ProjetoRepository
from app.schemas.checkpoint import (
    CheckpointResponse,
    CheckpointListResponse,
    CheckpointStartResponse,
    CheckpointDraftResponse,
    CheckpointSubmitResponse,
    AnexoResponse,
    AnexoListResponse,
)
from app.schemas.user import CurrentUser
from app.services.avaliacao_service import AvaliacaoService, CheckpointNotFoundError as AvaliacaoCheckpointNotFoundError
from app.ai.checkpoint_evaluator import CheckpointAIEvaluator
from app.ai.provider import FakeAIProvider
from app.ai.checkpoint_prompt import CheckpointEvaluationContext

logger = logging.getLogger(__name__)


class CheckpointNotFoundError(ValueError):
    pass


class CheckpointAlreadyExistsError(ValueError):
    pass


class CheckpointOrderError(ValueError):
    pass


class CheckpointAuthorizationError(ValueError):
    pass


class InvalidCheckpointTransitionError(ValueError):
    pass


class ProjetoNotFoundForCheckpointError(ValueError):
    pass


class AttachmentNotFoundError(ValueError):
    pass


class AttachmentLimitExceededError(ValueError):
    pass


class CheckpointValidationError(ValueError):
    def __init__(self, errors: list):
        self.errors = self._serialize_errors(errors)
        super().__init__(str(self.errors))

    def _serialize_errors(self, errors: list) -> list:
        serialized = []
        for err in errors:
            serialized_err = dict(err)
            # Convert tuple loc to list for JSON serialization
            if 'loc' in serialized_err and isinstance(serialized_err['loc'], tuple):
                serialized_err['loc'] = list(serialized_err['loc'])
            # Convert ctx ValueError to string for JSON serialization
            if 'ctx' in serialized_err and isinstance(serialized_err['ctx'], dict):
                ctx = serialized_err['ctx']
                for key, value in ctx.items():
                    if isinstance(value, BaseException):
                        ctx[key] = str(value)
            serialized.append(serialized_err)
        return serialized


class AttachmentRequiredError(ValueError):
    pass


class CheckpointService:
    def __init__(
        self,
        checkpoint_repo: CheckpointRepository,
        projeto_repo: ProjetoRepository,
        avaliacao_service: AvaliacaoService | None = None,
        ai_evaluator: CheckpointAIEvaluator | None = None,
    ):
        self.checkpoint_repo = checkpoint_repo
        self.projeto_repo = projeto_repo
        self.avaliacao_service = avaliacao_service
        self.ai_evaluator = ai_evaluator

    def list_checkpoints(
        self,
        projeto_id: UUID,
        current_user: CurrentUser,
    ) -> CheckpointListResponse:
        projeto = self._get_projeto_or_raise(projeto_id)
        self._authorize_view_checkpoint(projeto, current_user)

        checkpoints = self.checkpoint_repo.list_checkpoints_by_projeto(projeto_id)
        items = [CheckpointResponse.model_validate(cp) for cp in checkpoints]

        return CheckpointListResponse(items=items, total=len(items))

    def get_checkpoint(
        self,
        projeto_id: UUID,
        tipo: TipoCheckpoint,
        current_user: CurrentUser,
    ) -> CheckpointResponse:
        projeto = self._get_projeto_or_raise(projeto_id)
        self._authorize_view_checkpoint(projeto, current_user)

        checkpoint = self.checkpoint_repo.get_checkpoint_by_projeto_and_tipo(
            projeto_id, tipo
        )
        if not checkpoint:
            raise CheckpointNotFoundError("Checkpoint não encontrado")

        return CheckpointResponse.model_validate(checkpoint)

    def start_checkpoint(
        self,
        projeto_id: UUID,
        tipo: TipoCheckpoint,
        current_user: CurrentUser,
    ) -> CheckpointStartResponse:
        projeto = self._get_projeto_or_raise(projeto_id)
        self._authorize_manage_checkpoint(projeto, current_user)

        existing = self.checkpoint_repo.get_checkpoint_by_projeto_and_tipo(
            projeto_id, tipo
        )

        if existing:
            return self._handle_existing_checkpoint(existing, tipo)

        self._validate_checkpoint_order(projeto_id, tipo)

        now = datetime.now(timezone.utc)
        checkpoint = Checkpoint(
            projeto_id=projeto_id,
            tipo=tipo,
            status=StatusCheckpoint.EM_PREENCHIMENTO,
            iniciado_em=now,
            sugerido_em=None,
            concluido_em=None,
            respostas_formulario=None,
            resumo_para_marketing=None,
        )

        self.checkpoint_repo.create_checkpoint(checkpoint)
        return CheckpointStartResponse(
            checkpoint=CheckpointResponse.model_validate(checkpoint), criado=True
        )

    def _get_projeto_or_raise(self, projeto_id: UUID) -> Projeto:
        projeto = self.projeto_repo.get_project_by_id(projeto_id)
        if not projeto:
            raise ProjetoNotFoundForCheckpointError("Projeto não encontrado")
        return projeto

    def _authorize_view_checkpoint(self, projeto: Projeto, user: CurrentUser) -> None:
        if user.papel == PapelUsuario.VERTICAL:
            if projeto.vertical_id != user.vertical_id:
                raise CheckpointAuthorizationError("Acesso negado")
        elif user.papel == PapelUsuario.MARKETING:
            return
        elif user.papel == PapelUsuario.ADMIN:
            return
        elif user.papel == PapelUsuario.LIDERANCA:
            raise CheckpointAuthorizationError("Acesso negado")
        else:
            raise CheckpointAuthorizationError("Papel inválido")

    def _authorize_manage_checkpoint(self, projeto: Projeto, user: CurrentUser) -> None:
        if projeto.criado_por_id != user.id:
            raise CheckpointAuthorizationError("Apenas o criador pode iniciar checkpoint")

    def _validate_checkpoint_order(
        self, projeto_id: UUID, tipo: TipoCheckpoint
    ) -> None:
        if tipo == TipoCheckpoint.IDEACAO:
            return

        if tipo == TipoCheckpoint.DESENVOLVIMENTO:
            ideacao = self.checkpoint_repo.get_checkpoint_by_projeto_and_tipo(
                projeto_id, TipoCheckpoint.IDEACAO
            )
            if not ideacao or ideacao.status != StatusCheckpoint.CONCLUIDO:
                raise CheckpointOrderError(
                    "Checkpoint de Ideação deve estar CONCLUIDO antes de iniciar Desenvolvimento"
                )
            return

        if tipo == TipoCheckpoint.PRE_LANCAMENTO:
            desenvolvimento = self.checkpoint_repo.get_checkpoint_by_projeto_and_tipo(
                projeto_id, TipoCheckpoint.DESENVOLVIMENTO
            )
            if not desenvolvimento or desenvolvimento.status != StatusCheckpoint.CONCLUIDO:
                raise CheckpointOrderError(
                    "Checkpoint de Desenvolvimento deve estar CONCLUIDO antes de iniciar Pré-Lançamento"
                )
            return

    def _handle_existing_checkpoint(
        self, checkpoint: Checkpoint, tipo: TipoCheckpoint
    ) -> CheckpointStartResponse:
        if checkpoint.status == StatusCheckpoint.CONCLUIDO:
            return CheckpointStartResponse(
                checkpoint=CheckpointResponse.model_validate(checkpoint), criado=False
            )

        if checkpoint.status == StatusCheckpoint.EM_PREENCHIMENTO:
            return CheckpointStartResponse(
                checkpoint=CheckpointResponse.model_validate(checkpoint), criado=False
            )

        if checkpoint.status == StatusCheckpoint.SUGERIDO:
            # SUGERIDO mantido para compatibilidade futura (ex: sugestão automática de checkpoints)
            updates = {
                "status": StatusCheckpoint.EM_PREENCHIMENTO,
                "iniciado_em": datetime.now(timezone.utc),
            }
            self.checkpoint_repo.update_checkpoint(checkpoint, updates)
            return CheckpointStartResponse(
                checkpoint=CheckpointResponse.model_validate(checkpoint), criado=False
            )

        return CheckpointStartResponse(
            checkpoint=CheckpointResponse.model_validate(checkpoint), criado=False
        )

    def save_checkpoint_draft(
        self,
        projeto_id: UUID,
        tipo: TipoCheckpoint,
        respostas: dict,
        current_user: CurrentUser,
    ) -> CheckpointDraftResponse:
        projeto = self._get_projeto_or_raise(projeto_id)
        self._authorize_manage_checkpoint(projeto, current_user)

        checkpoint = self.checkpoint_repo.get_checkpoint_by_projeto_and_tipo(
            projeto_id, tipo
        )
        if not checkpoint:
            raise CheckpointNotFoundError("Checkpoint não encontrado")

        if checkpoint.status == StatusCheckpoint.CONCLUIDO:
            raise InvalidCheckpointTransitionError(
                "Checkpoint já concluído não pode ser editado"
            )

        now = datetime.now(timezone.utc)
        updates = {
            "respostas_formulario": respostas,
            "updated_at": now,
        }
        self.checkpoint_repo.update_checkpoint(checkpoint, updates)

        return CheckpointDraftResponse(
            checkpoint=CheckpointResponse.model_validate(checkpoint), salvo_em=now
        )

    def submit_checkpoint(
        self,
        projeto_id: UUID,
        tipo: TipoCheckpoint,
        respostas: dict,
        current_user: CurrentUser,
    ) -> CheckpointSubmitResponse:
        projeto = self._get_projeto_or_raise(projeto_id)
        self._authorize_manage_checkpoint(projeto, current_user)

        checkpoint = self.checkpoint_repo.get_checkpoint_by_projeto_and_tipo(
            projeto_id, tipo
        )
        if not checkpoint:
            raise CheckpointNotFoundError("Checkpoint não encontrado")

        if checkpoint.status == StatusCheckpoint.CONCLUIDO:
            raise InvalidCheckpointTransitionError(
                "Checkpoint já foi enviado"
            )

        self._validate_formulario(tipo, respostas)

        # Check if PRE_LANCAMENTO requires at least one attachment
        if tipo == TipoCheckpoint.PRE_LANCAMENTO:
            count = self.checkpoint_repo.count_attachments_by_checkpoint(checkpoint.id)
            if count == 0:
                raise AttachmentRequiredError(
                    "Checkpoint de Pré-Lançamento requer pelo menos um anexo"
                )

        now = datetime.now(timezone.utc)
        updates = {
            "respostas_formulario": respostas,
            "status": StatusCheckpoint.CONCLUIDO,
            "concluido_em": now,
            "updated_at": now,
        }
        self.checkpoint_repo.update_checkpoint(checkpoint, updates)

        # Trigger AI evaluation asynchronously (post-process)
        # IA falha não deve impedir a conclusão do checkpoint
        self._trigger_ai_evaluation(checkpoint, projeto_id, tipo, respostas, current_user)

        proxima_etapa = self._get_proxima_etapa(tipo)
        return CheckpointSubmitResponse(
            checkpoint=CheckpointResponse.model_validate(checkpoint),
            enviado_em=now,
            proxima_etapa=proxima_etapa,
        )

    def _trigger_ai_evaluation(
        self,
        checkpoint: Checkpoint,
        projeto_id: UUID,
        tipo: TipoCheckpoint,
        respostas: dict,
        current_user: CurrentUser,
    ) -> None:
        """Trigger AI evaluation as post-process. Failure does not affect checkpoint completion."""
        if not self.avaliacao_service or not self.ai_evaluator:
            logger.info("AI evaluation not configured, skipping")
            return

        try:
            # Build evaluation context
            context = self._build_evaluation_context(
                checkpoint=checkpoint,
                projeto_id=projeto_id,
                tipo=tipo,
                respostas=respostas,
            )

            # Call AI evaluator
            ia_output, metadata = self.ai_evaluator.evaluate(context)

            # Evaluate with engine and persist
            self.avaliacao_service.create_evaluation(
                checkpoint_id=checkpoint.id,
                ia_output=ia_output,
                modelo=metadata.modelo,
                prompt_version=metadata.prompt_version,
                criteria_version=metadata.criteria_version,
                prompt_hash=metadata.prompt_hash,
                criteria_hash=metadata.criteria_hash,
            )

            logger.info(f"AI evaluation completed for checkpoint {checkpoint.id}")

        except Exception as e:
            # Log error but don't fail the checkpoint
            logger.warning(f"AI evaluation failed for checkpoint {checkpoint.id}: {type(e).__name__}: {e}")

    def _build_evaluation_context(
        self,
        checkpoint: Checkpoint,
        projeto_id: UUID,
        tipo: TipoCheckpoint,
        respostas: dict,
    ) -> CheckpointEvaluationContext:
        """Build evaluation context from checkpoint data."""
        # Extract form version info from respostas_formulario if available
        form_data = checkpoint.respostas_formulario or {}
        versao_formulario = form_data.get("versao_formulario", f"{tipo.value.lower()}_v1")
        versao_business = form_data.get("versao_business", "2026-07")
        schema_version = form_data.get("schema_version", 1)

        # Extract attachments metadata
        anexos = form_data.get("anexos", [])

        # Previous evaluations (if any) - could be extended later
        avaliacoes_anteriores = []

        return CheckpointEvaluationContext(
            checkpoint_id=checkpoint.id,
            projeto_id=projeto_id,
            tipo_checkpoint=tipo,
            versao_formulario=versao_formulario,
            versao_business=versao_business,
            schema_version=schema_version,
            respostas=respostas,
            anexos=anexos,
            avaliacoes_anteriores=avaliacoes_anteriores,
            conversa_resumida=None,  # Could be extended later
        )

    def _validate_formulario(self, tipo: TipoCheckpoint, respostas: dict) -> None:
        try:
            if tipo == TipoCheckpoint.IDEACAO:
                from app.schemas.checkpoint import IdeacaoFormEnvelope

                IdeacaoFormEnvelope(
                    versao_formulario="ideacao_v1",
                    versao_business="2026-07",
                    schema_version=1,
                    tipo_checkpoint=tipo,
                    respostas=respostas,
                )
            elif tipo == TipoCheckpoint.DESENVOLVIMENTO:
                from app.schemas.checkpoint import DesenvolvimentoFormEnvelope

                DesenvolvimentoFormEnvelope(
                    versao_formulario="desenvolvimento_v1",
                    versao_business="2026-07",
                    schema_version=1,
                    tipo_checkpoint=tipo,
                    respostas=respostas,
                )
            elif tipo == TipoCheckpoint.PRE_LANCAMENTO:
                from app.schemas.checkpoint import PreLancamentoFormEnvelope

                PreLancamentoFormEnvelope(
                    versao_formulario="pre_lancamento_v1",
                    versao_business="2026-07",
                    schema_version=1,
                    tipo_checkpoint=tipo,
                    respostas=respostas,
                )
        except ValidationError as e:
            raise CheckpointValidationError(e.errors())
        except ValueError as e:
            # Custom validators raise ValueError, wrap in CheckpointValidationError
            raise CheckpointValidationError([{"msg": str(e), "type": "value_error"}])
        except Exception as e:
            # Catch any other unexpected errors
            raise CheckpointValidationError([{"msg": str(e), "type": "validation_error"}])

    def _get_proxima_etapa(self, tipo: TipoCheckpoint) -> str | None:
        if tipo == TipoCheckpoint.IDEACAO:
            return "Iniciar Checkpoint de Desenvolvimento"
        if tipo == TipoCheckpoint.DESENVOLVIMENTO:
            return "Iniciar Checkpoint de Pré-Lançamento"
        return None

    def list_attachments(
        self,
        projeto_id: UUID,
        tipo: TipoCheckpoint,
        current_user: CurrentUser,
    ) -> AnexoListResponse:
        projeto = self._get_projeto_or_raise(projeto_id)
        self._authorize_view_checkpoint(projeto, current_user)

        checkpoint = self.checkpoint_repo.get_checkpoint_by_projeto_and_tipo(
            projeto_id, tipo
        )
        if not checkpoint:
            raise CheckpointNotFoundError("Checkpoint não encontrado")

        anexos = self.checkpoint_repo.list_attachments_by_checkpoint(checkpoint.id)
        items = [AnexoResponse.model_validate(a) for a in anexos]

        return AnexoListResponse(items=items, total=len(items))

    def register_attachment(
        self,
        projeto_id: UUID,
        tipo: TipoCheckpoint,
        storage_key: str,
        nome_original: str,
        mime_type: str,
        tamanho_bytes: int,
        current_user: CurrentUser,
    ) -> AnexoResponse:
        projeto = self._get_projeto_or_raise(projeto_id)
        self._authorize_manage_checkpoint(projeto, current_user)

        checkpoint = self.checkpoint_repo.get_checkpoint_by_projeto_and_tipo(
            projeto_id, tipo
        )
        if not checkpoint:
            raise CheckpointNotFoundError("Checkpoint não encontrado")

        if checkpoint.status == StatusCheckpoint.CONCLUIDO:
            raise InvalidCheckpointTransitionError(
                "Checkpoint concluído não aceita novos anexos"
            )

        count = self.checkpoint_repo.count_attachments_by_checkpoint(checkpoint.id)
        if count >= 10:
            raise AttachmentLimitExceededError(
                "Limite de 10 anexos por checkpoint atingido"
            )

        anexo = AnexoCheckpoint(
            checkpoint_id=checkpoint.id,
            nome_original=nome_original,
            mime_type=mime_type,
            tamanho_bytes=tamanho_bytes,
            storage_key=storage_key,
            enviado_por_id=current_user.id,
        )
        self.checkpoint_repo.create_attachment(anexo)

        return AnexoResponse.model_validate(anexo)

    def delete_attachment(
        self,
        projeto_id: UUID,
        tipo: TipoCheckpoint,
        anexo_id: UUID,
        current_user: CurrentUser,
    ) -> None:
        projeto = self._get_projeto_or_raise(projeto_id)
        self._authorize_manage_checkpoint(projeto, current_user)

        checkpoint = self.checkpoint_repo.get_checkpoint_by_projeto_and_tipo(
            projeto_id, tipo
        )
        if not checkpoint:
            raise CheckpointNotFoundError("Checkpoint não encontrado")

        anexo = self.checkpoint_repo.get_attachment_by_id_and_checkpoint(
            anexo_id, checkpoint.id
        )
        if not anexo:
            raise AttachmentNotFoundError("Anexo não encontrado")

        self.checkpoint_repo.delete_attachment(anexo)